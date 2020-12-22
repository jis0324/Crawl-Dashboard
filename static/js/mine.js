$(document).ready(function () {

  // datatable for domains
  $('#domains_tbl').removeAttr('width').DataTable({
    "sPaginationType": "full_numbers",
    "bJQueryUI": true,
    "bAutoWidth": false, // Disable the auto width calculation
    "aoColumns": [
      { "sWidth": "10%" },
      { "sWidth": "10%" },
      { "sWidth": "25%" },
      { "sWidth": "5%" },
      { "sWidth": "10%" },
      { "sWidth": "10%" },
      { "sWidth": "10%" },
      { "sWidth": "10%" },
      { "sWidth": "10%" },
    ]
  }).order([0, 'asc']).draw();

 // datatable for crawlers
  $('#crawlers_tbl').DataTable({
  }).order([0, 'desc']).draw();

  // datatable for inventory
  $('#crawler_summary_tbl').removeAttr('width').DataTable({
    "sPaginationType": "full_numbers",
    "bJQueryUI": true,
    "bAutoWidth": false, // Disable the auto width calculation
    "aoColumns": [
      { "sWidth": "8%" },
      { "sWidth": "10%" },
      { "sWidth": "25%" },
      { "sWidth": "5%" },
      { "sWidth": "10%" },
      { "sWidth": "8%" },
      { "sWidth": "7%" },
      { "sWidth": "5%" },
      { "sWidth": "7%" },
      { "sWidth": "10%" },
      { "sWidth": "5%" },
    ]
  }).order([0, 'asc']).draw();

  // datatable for inventory
  $('#total_summary_tbl').removeAttr('width').DataTable({
    "sPaginationType": "full_numbers",
    "bJQueryUI": true,
    "bAutoWidth": false, // Disable the auto width calculation
    "aoColumns": [
      { "sWidth": "8%" },
      { "sWidth": "10%" },
      { "sWidth": "25%" },
      { "sWidth": "5%" },
      { "sWidth": "10%" },
      { "sWidth": "8%" },
      { "sWidth": "7%" },
      { "sWidth": "5%" },
      { "sWidth": "7%" },
      { "sWidth": "10%" },
      { "sWidth": "5%" },
    ]
  }).order([0, 'asc']).draw();

  // datatable for test list
  $('#view_test_tbl').DataTable({
  }).order([0, 'asc']).draw();

  // datatable for inventory
  $('#crawler_inventory_tbl').removeAttr('width').DataTable({
    "sPaginationType": "full_numbers",
    "bJQueryUI": true,
    "bAutoWidth": false, // Disable the auto width calculation
    "aoColumns": [
      { "sWidth": "8%" },
      { "sWidth": "10%" },
      { "sWidth": "20%" },
      { "sWidth": "7%" },
      { "sWidth": "5%" },
      { "sWidth": "5%" },
      { "sWidth": "5%" },
      { "sWidth": "15%" },
      { "sWidth": "5%" },
      { "sWidth": "5%" },
      { "sWidth": "5%" },
      { "sWidth": "5%" },
      { "sWidth": "5%" },
    ]
  }).order([0, 'asc']).draw();

  // datatable for inventory
  $('#test_view_detail_inventory_tbl').DataTable({
  }).order([0, 'asc']).draw();

  // datatable for unexpected urls table
  $('#unexpected_urls_tbl').DataTable({
  }).order([0, 'asc']).draw();

  // datatable for crawl status table
  $('#crawl_status_tbl').DataTable({
  }).order([0, 'asc']).draw();

  $('#domains_tbl').on('click', '.test-btn', function() {
    show_loading();
    let btn = $(this);
    $.ajax({
      type: "POST",
      url: "/domains/test_domain/",
      data: {
        'csrfmiddlewaretoken' : $('#domains_tbl input[name="csrfmiddlewaretoken"]').val(),
        'dealer_id': $(this).data('dealer'),
        'dealer_name': $(this).data('name'),
        'dealer_city': $(this).data('city'),
        'dealer_state': $(this).data('state'),
        'dealer_zip': $(this).data('zip'),
        'dealer_website': $(this).data('website'),
        'dealer_category': $(this).data('category'),
        'dealer_type': $(this).data('type'),
        'dealer_redirect': $(this).data('redirect'),
      },
      success: function (result) {
        let response = JSON.parse(result);
        if (response['status'] == 'crawling') {
          alert('Crawling Test Engin is running by ' + response['user'], 'Please wait for a long time.')
        }
        else if (response['status'] == 'success') {
          alert('Crawling Test Engine run by ' + response['user'] + ' successfully.')
          btn.addClass('d-none');
          btn.parent().find('.cancel-btn').removeClass('d-none');
        } else {
          alert('Raised Some Error! Please try again.')
        }
        hide_loading();
      }
    });
  });

  $('#domains_tbl').on('click', '.cancel-btn', function() {
    let btn = $(this);
    if (confirm('Really cancel?')) {
      show_loading();
      $.ajax({
        type: "POST",
        url: "/domains/test_cancel/",
        data: {
          'csrfmiddlewaretoken' : $('#domains_tbl input[name="csrfmiddlewaretoken"]').val(),
          'dealer_id': $(this).data('dealer'),
        },
        success: function (result) {
          if (result == 'success') {
            btn.addClass('d-none');
            btn.parent().find('.test-btn').removeClass('d-none');
            btn.parent().find('.view-btn').removeClass('d-none');
          } else if (result == 'complete') {
            alert('Process already completed.')
            btn.addClass('d-none');
            btn.parent().find('.test-btn').removeClass('d-none');
            btn.parent().find('.view-btn').removeClass('d-none');
          } else {
            alert('Raised Some Error! Please try again.');
          }
          hide_loading();
        }
      });
    }
  });

  $('table').on('click', '.edit-btn', function() {
    event.preventDefault();
    show_loading();
    let dealer_domain = $(this).data('dealer');
    $('#edit_domain_modal #edit_domain').val('');
    $('#edit_domain_modal #edit_website').val('');
    $('#edit_domain_modal #edit_inputdata').val('');
    $('#edit_domain_modal #edit_crawl_type').val('');
    $('#edit_domain_modal #edit_crawl_type_reason').val('');
    $('#edit_domain_modal #edit_redirect_urls').val('');
    $('#edit_domain_modal #edit_makes').val('');
    $('#edit_domain_modal #edit_get_desc').val('');

    $.ajax({
      type: "POST",
      url: "/domains/get_dealer/",
      data: {
        'csrfmiddlewaretoken' : $('#edit_domain_form input[name="csrfmiddlewaretoken"]').val(),
        'domain': dealer_domain,
      },
      success: function (result) {
        if (result == 'not_found') {
          alert('Can not found this dealer! Try again.');
        } else if (result == 'failed') {
          alert('Raised Some Error! Please try again.');
        } else {
          let response = JSON.parse(result);
          
          $('#edit_domain_modal #edit_domain').val(response['domain']);
          $('#edit_domain_modal #edit_website').val(response['website']);
          $('#edit_domain_modal #edit_inputdata').val(response['domain_inputdata']);
          $('#edit_domain_modal #edit_crawl_type').val(response['dealer_type']);
          $('#edit_domain_modal #edit_crawl_type_reason').val(response['dealer_type_reason']);
          $('#edit_domain_modal #edit_redirect_urls').val(response['dealer_redirect']);
          $('#edit_domain_modal #edit_makes').val(response['makes']);
          if (response['get_description'] == "") {
            $('#edit_domain_modal #edit_get_desc').val("N");
          } else {
            $('#edit_domain_modal #edit_get_desc').val("Y");
          };

          $('#edit_domain_modal').modal();
        }
        hide_loading();
      }
    });

  });

  $('#edit_domain_form').submit(function () {
    event.preventDefault();
    show_loading();

    $.ajax({
      type: "POST",
      url: "/domains/update_input/",
      data: {
        'csrfmiddlewaretoken' : $('#edit_domain_form input[name="csrfmiddlewaretoken"]').val(),
        'domain': $('#edit_domain_modal #edit_domain').val(),
        'website': $('#edit_domain_modal #edit_website').val(),
        'inputdata': $('#edit_domain_modal #edit_inputdata').val(),
        'redirect_urls': $('#edit_domain_modal #edit_redirect_urls').val(),
        'makes': $('#edit_domain_modal #edit_makes').val(),
        'get_description': $('#edit_domain_modal #edit_get_desc').val(),
        'crawl_type': $('#edit_domain_modal #edit_crawl_type').val(),
        'crawl_type_reason': $('#edit_domain_modal #edit_crawl_type_reason').val(),
      },
      success: function (result) {
        if (result == 'success') {
          $('#edit_domain_modal').modal('hide');
        } else {
          alert('Raised Some Error! Please try again.');
        }
        hide_loading();
      }
    });

  });

  $('#settings_form .setting-edit-btn').on('click', function() {
    $('#settings_form input').removeAttr('disabled');
    $('#settings_form textarea').removeAttr('disabled');
    $('#settings_form select').removeAttr('disabled');
    $(this).removeClass('d-block').addClass('d-none');
    $('#settings_form .setting-submit-btn').removeClass('d-none').addClass('d-block');
  });

  $('#settings_form').submit(function() {
    event.preventDefault();
    show_loading();

    $.ajax({
      type: "POST",
      url: "/settings/",
      data: {
        'csrfmiddlewaretoken' : $('#settings_form input[name="csrfmiddlewaretoken"]').val(),
        "host" : $('#settings_form #setting_host').val(),
        "port" : $('#settings_form #setting_port').val(),
        "crawler_interval_time" : $('#settings_form #setting_interval_time').val(),
        "crawler_start_time" : $('#settings_form #setting_start_time').val(),
        "process_per_crawler" : $('#settings_form #setting_process_count').val(),
        "not_available_request_repeat_count" : $('#settings_form #setting_not_available_repeat_count').val(),
        "browseable_process_num" : $('#settings_form #setting_browseable_process_num').val(),
        "browseable_thread_count" : $('#settings_form #setting_browseable_thread_count').val(),
        "update_status" : $('#settings_form #setting_crawler_file_update_flag').val(),
        "dealer_list_reinsert_flag" : $('#settings_form #setting_dealer_list_reinsert_flag').val(),
        "crawlable_crawlers" : $('#settings_form #setting_scrapy_crawlers').val(),
        "browseable_crawlers" : $('#settings_form #setting_selenium_crawlers').val(),
      },
      success: function (result) {
        if (result == 'success') {
          $('#settings_form input').prop( "disabled", true );
          $('#settings_form textarea').prop( "disabled", true );
          $('#settings_form select').prop( "disabled", true );
          $('#settings_form .setting-edit-btn').removeClass('d-none').addClass('d-block');
          $('#settings_form .setting-submit-btn').removeClass('d-block').addClass('d-none');
        } else {
          alert('Raised Some Error! Please try again.');
        }
        hide_loading();
      }
    });
  });

  hide_loading();

  $('#domains_tbl').removeClass('d-none');
  $('#total_summary_tbl').removeClass('d-none');
  $('#crawler_summary_tbl').removeClass('d-none');

});

function show_loading() {
  $('.loading-section').removeClass('d-none');
  $('.navbar').css('opacity', .6);
  $('.main-container').css('opacity', .6);
};

function hide_loading() {
  $('.loading-section').addClass('d-none');
  $('.navbar').css('opacity', 1);
  $('.main-container').css('opacity', 1);
};

function redirect(event) {
  event.preventDefault();
  show_loading();
  var href = event.currentTarget.getAttribute('href');
  window.location = href;
}