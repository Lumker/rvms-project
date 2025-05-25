// static/js/datatables-setup.js
function initializeDataTable(tableId, options) {
    // Preserve sidebar toggle functionality
    var originalSidebarToggle = $('.sidebar-toggle').clone(true);
    
    // Default options
    var defaultOptions = {
        responsive: true,
        searching: true,
        ordering: true,
        paging: true,
        info: true,
        language: {
            search: '<span>Search:</span> _INPUT_',
            searchPlaceholder: 'Search...',
            lengthMenu: '<span>Show:</span> _MENU_',
            paginate: {
                first: 'First',
                last: 'Last',
                next: 'Next',
                previous: 'Previous'
            }
        }
    };
    
    // Merge default options with provided options
    var finalOptions = $.extend({}, defaultOptions, options);
    
    // Initialize DataTable
    var table = $(tableId).DataTable(finalOptions);
    
    // Restore sidebar toggle functionality
    $('.sidebar-toggle').off('click');
    $('.sidebar-toggle').on('click', function(e) {
        e.preventDefault();
        $('body').toggleClass('mini-sidebar');
    });
    
    // Style the DataTable elements
    $('.dataTables_filter input').addClass('form-control form-control-sm');
    $('.dataTables_length select').addClass('custom-select custom-select-sm form-control form-control-sm');
    
    return table;
}