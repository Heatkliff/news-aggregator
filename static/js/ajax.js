// AJAX Pagination and Filtering script

$(document).ready(function() {
    // Initialize flatpickr for date range picker
    let dateRangePicker = flatpickr("#dateRange", {
        mode: "range",
        dateFormat: "Y-m-d",
        allowInput: true,
        clickOpens: true,
        onChange: function(selectedDates, dateStr, instance) {
            // Store the date range value
            if (selectedDates.length === 1) {
                // Single date selected
                instance.element.value = flatpickr.formatDate(selectedDates[0], "Y-m-d");
            } else if (selectedDates.length === 2) {
                // Date range selected
                instance.element.value = flatpickr.formatDate(selectedDates[0], "Y-m-d") + 
                                       " to " + 
                                       flatpickr.formatDate(selectedDates[1], "Y-m-d");
            }
        }
    });

    // Clear dates button functionality
    $('#clearDates').on('click', function() {
        dateRangePicker.clear();
    });

    // Filter collapsing functionality
    $('.filter-header').on('click', function() {
        const target = $(this).data('toggle');
        const content = $('#' + target + 'Content');
        const icon = $(this).find('.filter-collapse-icon');
        
        content.slideToggle(300);
        icon.toggleClass('collapsed');
    });

    // Tag search functionality
    $('#tagSearch').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        const tagItems = $('.tag-item');
        
        if (searchTerm === '') {
            // Show all tags in original order if search is empty
            tagItems.show().sort(function(a, b) {
                return $(a).find('label').text().localeCompare($(b).find('label').text());
            }).appendTo('#tagCheckboxGroup');
        } else {
            // Filter and sort tags
            let matchingTags = [];
            let nonMatchingTags = [];
            
            tagItems.each(function() {
                const tagName = $(this).data('tag-name');
                if (tagName.includes(searchTerm)) {
                    if (tagName.startsWith(searchTerm)) {
                        // Tags that start with search term go first
                        matchingTags.unshift(this);
                    } else {
                        // Tags that contain search term go after
                        matchingTags.push(this);
                    }
                    $(this).show();
                } else {
                    nonMatchingTags.push(this);
                    $(this).hide();
                }
            });
            
            // Reorder matching tags to show starts-with first
            const container = $('#tagCheckboxGroup');
            matchingTags.forEach(function(tag) {
                container.append(tag);
            });
        }
    });

    // Mobile filter toggle
    $('#mobileFilterToggle').on('click', function() {
        const sidebar = $('#filtersSidebar');
        const button = $(this);
        
        sidebar.toggleClass('show');
        
        if (sidebar.hasClass('show')) {
            button.html('<i class="fas fa-times"></i> Hide Filters');
        } else {
            button.html('<i class="fas fa-filter"></i> Show Filters');
        }
    });

    // Function to get all current filter values
    function getFilters() {
        const filters = {
            q: $('input[name="q"]').val() || ''
        };
        
        // Get multiple selected sources
        const sources = [];
        $('input[name="source"]:checked').each(function() {
            sources.push($(this).val());
        });
        if (sources.length > 0) {
            filters.source = sources;
        }
        
        // Get multiple selected categories
        const categories = [];
        $('input[name="category"]:checked').each(function() {
            categories.push($(this).val());
        });
        if (categories.length > 0) {
            filters.category = categories;
        }
        
        // Get multiple selected tags
        const tags = [];
        $('input[name="tag"]:checked').each(function() {
            tags.push($(this).val());
        });
        if (tags.length > 0) {
            filters.tag = tags;
        }
        
        // Get date range
        const dateRange = $('#dateRange').val();
        if (dateRange) {
            filters.date_range = dateRange;
        }
        
        // Get sort order
        filters.sort = $('#sortBy').val();
        
        return filters;
    }
    
    // Function to load news via AJAX
    function loadNews(page) {
        // Get filter values
        const filters = getFilters();
        
        // Add page number to filters
        if (page) {
            filters.page = page;
        }
        
        // Show loading indicator
        $('#news-container').html('<div class="text-center p-5"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>');
        
        // Make AJAX request
        $.ajax({
            url: window.location.pathname,
            data: filters,
            traditional: true, // Important for handling arrays in jQuery AJAX
            dataType: 'html',
            success: function(data) {
                // Extract news container content from response
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = data;
                const newContent = $(tempDiv).find('#news-container').html();
                const pagination = $(tempDiv).find('.pagination').html();
                
                // Update the page
                $('#news-container').html(newContent);
                $('.pagination').html(pagination);
                
                // Rebind pagination events
                bindPaginationEvents();
                
                // Update URL with new query params
                updateURL(filters);
                
                // Hide mobile filters after applying (optional)
                if (window.innerWidth <= 991) {
                    $('#filtersSidebar').removeClass('show');
                    $('#mobileFilterToggle').html('<i class="fas fa-filter"></i> Show Filters');
                }
            },
            error: function() {
                $('#news-container').html('<div class="alert alert-danger">Error loading news. Please try again.</div>');
            }
        });
    }
    
    // Function to update URL with filter parameters
    function updateURL(params) {
        if (!history.pushState) return; // Check browser support
        
        const url = window.location.protocol + "//" + window.location.host + window.location.pathname;
        
        // Build query string from filters, handling arrays properly
        const queryParts = [];
        for (const key in params) {
            if (params[key]) {
                if (Array.isArray(params[key])) {
                    // Handle multiple values for the same parameter
                    params[key].forEach(function(value) {
                        queryParts.push(encodeURIComponent(key) + '=' + encodeURIComponent(value));
                    });
                } else {
                    queryParts.push(encodeURIComponent(key) + '=' + encodeURIComponent(params[key]));
                }
            }
        }
        
        const queryString = queryParts.join('&');
        const finalUrl = queryString ? url + '?' + queryString : url;
        
        // Update browser URL without reloading the page
        window.history.pushState({path: finalUrl}, '', finalUrl);
    }
    
    // Function to bind click events to pagination links
    function bindPaginationEvents() {
        $('.pagination .page-link').off('click').on('click', function(e) {
            e.preventDefault();
            
            let page = $(this).data('page');
            if (!page) {
                // Extract page number from href attribute if data-page is not set
                const href = $(this).attr('href');
                const pageMatch = href.match(/page=(\d+)/);
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
    
    // Form submission handler
    $('#filterForm').on('submit', function(e) {
        e.preventDefault();
        loadNews(1); // Load first page with new filters
    });
    
    // Clear all filters functionality
    $('#clearFilters').on('click', function() {
        // Clear all checkboxes
        $('#filterForm input[type="checkbox"]').prop('checked', false);
        
        // Clear date range
        dateRangePicker.clear();
        
        // Reset sort to default
        $('#sortBy').val('-created_at');
        
        // Clear tag search
        $('#tagSearch').val('').trigger('input');
        
        // Clear search query
        $('input[name="q"]').val('');
        
        // Load news with cleared filters
        loadNews(1);
    });
    
    // Initialize filters from URL parameters on page load
    function initializeFiltersFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        
        // Set source checkboxes
        const sources = urlParams.getAll('source');
        sources.forEach(function(source) {
            $('input[name="source"][value="' + source + '"]').prop('checked', true);
        });
        
        // Set category checkboxes
        const categories = urlParams.getAll('category');
        categories.forEach(function(category) {
            $('input[name="category"][value="' + category + '"]').prop('checked', true);
        });
        
        // Set tag checkboxes
        const tags = urlParams.getAll('tag');
        tags.forEach(function(tag) {
            $('input[name="tag"][value="' + tag + '"]').prop('checked', true);
        });
        
        // Set date range
        const dateRange = urlParams.get('date_range');
        if (dateRange) {
            $('#dateRange').val(dateRange);
            // Parse and set the flatpickr dates
            if (dateRange.includes(' to ')) {
                const dates = dateRange.split(' to ');
                dateRangePicker.setDate([dates[0].trim(), dates[1].trim()]);
            } else {
                dateRangePicker.setDate([dateRange.trim()]);
            }
        }
        
        // Set sort order
        const sort = urlParams.get('sort');
        if (sort) {
            $('#sortBy').val(sort);
        }
    }
    
    // Initialize filters on page load
    initializeFiltersFromURL();
});