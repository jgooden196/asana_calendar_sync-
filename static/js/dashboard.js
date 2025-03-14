document.addEventListener('DOMContentLoaded', function() {
    const syncButton = document.getElementById('sync-button');
    const syncStatus = document.getElementById('sync-status');
    const syncResults = document.getElementById('sync-results');
    const tasksFoundEl = document.getElementById('tasks-found');
    const eventsCreatedEl = document.getElementById('events-created');
    const alreadySyncedEl = document.getElementById('already-synced');
    const errorsEl = document.getElementById('errors');
    const lastSyncTimeEl = document.getElementById('last-sync-time');
    const syncedTasksList = document.getElementById('synced-tasks-list');
    
    // Helper function to format dates
    function formatDateTime(isoString) {
        const date = new Date(isoString);
        return date.toLocaleString();
    }
    
    // Function to update the sync results display
    function updateResults(stats, timestamp) {
        tasksFoundEl.textContent = stats.tasks_found;
        eventsCreatedEl.textContent = stats.events_created;
        alreadySyncedEl.textContent = stats.already_synced;
        errorsEl.textContent = stats.errors;
        
        lastSyncTimeEl.textContent = `Last synced: ${formatDateTime(timestamp)}`;
        syncResults.style.display = 'block';
        
        // If any events were created, refresh the page after 2 seconds
        // to update the synced tasks list
        if (stats.events_created > 0) {
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        }
    }
    
    // Set up sync button click handler
    syncButton.addEventListener('click', function() {
        // Update button state to show syncing
        syncButton.disabled = true;
        syncButton.innerHTML = '<span class="spinner-border spinner-border-sm sync-spinner" role="status" aria-hidden="true"></span> Syncing...';
        
        // Update status
        syncStatus.innerHTML = '<i class="bi bi-arrow-repeat sync-animate"></i> Synchronization in progress...';
        
        // Call the sync API endpoint
        fetch('/api/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Sync request failed');
            }
            return response.json();
        })
        .then(data => {
            // Update button state
            syncButton.disabled = false;
            syncButton.innerHTML = '<i class="bi bi-arrow-repeat"></i> Sync Tasks to Calendar';
            
            // Update status
            if (data.stats.errors > 0) {
                syncStatus.innerHTML = '<i class="bi bi-exclamation-triangle text-warning"></i> Sync completed with some errors';
            } else {
                syncStatus.innerHTML = '<i class="bi bi-check-circle text-success"></i> Sync completed successfully';
            }
            
            // Update results display
            updateResults(data.stats, data.timestamp);
        })
        .catch(error => {
            console.error('Error during sync:', error);
            
            // Update button state
            syncButton.disabled = false;
            syncButton.innerHTML = '<i class="bi bi-arrow-repeat"></i> Sync Tasks to Calendar';
            
            // Update status
            syncStatus.innerHTML = '<i class="bi bi-x-circle text-danger"></i> Sync failed. Please try again.';
        });
    });
});
