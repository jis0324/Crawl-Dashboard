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