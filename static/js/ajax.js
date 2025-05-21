// AJAX Pagination and Filtering script

$(document).ready(function() {
    // Function to get all current filter values
    function getFilters() {
        return {
            source: $('#sourceFilter').val(),
            category: $('#categoryFilter').val(),
            tag: $('#tagFilter').val(),
            date: $('#dateFilter').val(),
            sort: $('#sortBy').val(),
            q: $('input[name="q"]').val()
        };
    }
    
    // Function to load news via AJAX
    function loadNews(page) {
        // Get filter values
        var filters = getFilters();
        
        // Add page number to filters
        filters.page = page;
        
        // Show loading indicator
        $('#news-container').html('<div class="text-center p-5"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>');
        
        // Make AJAX request
        $.ajax({
            url: window.location.pathname,  // current URL path
            data: filters,
            dataType: 'html',
            success: function(data) {
                // Extract news container content from response
                var tempDiv = document.createElement('div');
                tempDiv.innerHTML = data;
                var newContent = $(tempDiv).find('#news-container').html();
                var pagination = $(tempDiv).find('.pagination').html();
                
                // Update the page
                $('#news-container').html(newContent);
                $('.pagination').html(pagination);
                
                // Rebind pagination events
                bindPaginationEvents();
                
                // Update URL with new query params
                updateURL(filters);
            },
            error: function() {
                $('#news-container').html('<div class="alert alert-danger">Error loading news. Please try again.</div>');
            }
        });
    }
    
    // Function to update URL with filter parameters
    function updateURL(params) {
        if (!history.pushState) return; // Check browser support
        
        var url = window.location.protocol + "//" + window.location.host + window.location.pathname;
        
        // Build query string from filters, removing empty values
        var queryParts = [];
        for (var key in params) {
            if (params[key]) {
                queryParts.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key]));
            }
        }
        
        var queryString = queryParts.join('&');
        
        if (queryString) {
            url += '?' + queryString;
        }
        
        // Update browser URL without reloading the page
        window.history.pushState({path: url}, '', url);
    }
    
    // Function to bind click events to pagination links
    function bindPaginationEvents() {
        $('.pagination .page-link').on('click', function(e) {
            e.preventDefault();
            
            var page = $(this).data('page');
            if (!page) {
                // Extract page number from href attribute if data-page is not set
                var href = $(this).attr('href');
                var pageMatch = href.match(/page=(\d+)/);
                if (pageMatch) {
                    page = pageMatch[1];
                }
            }
            
            if (page) {
                loadNews(page);
                
                // Scroll to top of news container
                $('html, body').animate({
                    scrollTop: $('#news-container').offset().top - 100
                }, 200);
            }
        });
    }
    
    // Initial binding
    bindPaginationEvents();
    
    // Filter changes
    $('#sourceFilter, #categoryFilter, #tagFilter, #dateFilter, #sortBy').on('change', function() {
        loadNews(1); // Reset to first page when filter changes
    });
});
