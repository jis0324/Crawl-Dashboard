$(document).ready(function () {

  // datatable for domains
  $('#domains_tbl').DataTable({
  }).order([0, 'asc']).draw();

 // datatable for crawlers
  $('#crawlers_tbl').DataTable({
  }).order([0, 'desc']).draw();

  // datatable for inventory
  $('#crawler_summary_tbl').DataTable({
  }).order([0, 'asc']).draw();

  // datatable for inventory
  $('#total_summary_tbl').DataTable({
  }).order([0, 'asc']).draw();

  // datatable for test list
  $('#view_test_tbl').DataTable({
  }).order([0, 'asc']).draw();

  // datatable for inventory
  $('#crawler_inventory_tbl').DataTable({
  }).order([0, 'asc']).draw();

  // datatable for inventory
  $('#test_view_detail_inventory_tbl').DataTable({
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
    let dealer_id = $(this).data('dealer');
    $('#edit_domain_modal #edit_dealer_id').val('');
    $('#edit_domain_modal #edit_dealer_name').val('');
    $('#edit_domain_modal #edit_dealer_domain').val('');
    $('#edit_domain_modal #edit_crawl_type').val('');
    $('#edit_domain_modal #edit_crawl_type_reason').val('');
    $('#edit_domain_modal #edit_redirect_urls').val('');

    $.ajax({
      type: "POST",
      url: "/domains/get_dealer/",
      data: {
        'csrfmiddlewaretoken' : $('#edit_domain_form input[name="csrfmiddlewaretoken"]').val(),
        'dealer_id': dealer_id,
      },
      success: function (result) {
        if (result == 'not_found') {
          alert('Can not found this dealer! Try again.');
        } else if (result == 'failed') {
          alert('Raised Some Error! Please try again.');
        } else {
          let response = JSON.parse(result);
          
          $('#edit_domain_modal #edit_dealer_id').val(response['dealer_id']);
          $('#edit_domain_modal #edit_dealer_name').val(response['dealer_name']);
          $('#edit_domain_modal #edit_dealer_domain').val(response['dealer_site']);
          $('#edit_domain_modal #edit_crawl_type').val(response['dealer_type']);
          $('#edit_domain_modal #edit_crawl_type_reason').val(response['dealer_type_reason']);
          $('#edit_domain_modal #edit_redirect_urls').val(response['dealer_redirect']);

          $('#edit_domain_modal').modal();
        }
        hide_loading();
      }
    });

  });

  $('#edit_domain_form').submit(function () {
    event.preventDefault();
    show_loading();
    let dealer_id = $('#edit_domain_modal #edit_dealer_id').val();
    let redirect_urls = $('#edit_domain_modal #edit_redirect_urls').val();
    let crawl_type = $('#edit_domain_modal #edit_crawl_type').val();
    let crawl_type_reason = $('#edit_domain_modal #edit_crawl_type_reason').val();

    $.ajax({
      type: "POST",
      url: "/domains/update_input/",
      data: {
        'csrfmiddlewaretoken' : $('#edit_domain_form input[name="csrfmiddlewaretoken"]').val(),
        'dealer_id': dealer_id,
        'redirect_urls': redirect_urls,
        'crawl_type': crawl_type,
        'crawl_type_reason': crawl_type_reason,
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
        "crawler_start_time" : $('#settings_form #setting_start_time').val(),
        "crawler_interval_time" : $('#settings_form #setting_interval_time').val(),
        "url_per_spider_crawler" : $('#settings_form #setting_url_count_per_scrapy_crawler').val(),
        "url_per_selenium_crawler" : $('#settings_form #setting_url_count_per_selenium_crawler').val(),
        "spider_crawlers" : $('#settings_form #setting_scrapy_crawlers').val(),
        "selenium_crawlers" : $('#settings_form #setting_selenium_crawlers').val(),
        "update_status" : $('#settings_form #setting_crawler_file_update_flag').val(),
        "process_per_crawler" : $('#settings_form #setting_process_count').val(),
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

  $('#domains_tbl').removeClass('d-none');

  hide_loading();
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