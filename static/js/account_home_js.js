$(document).ready(function () {
    $('#add-menu').click(function () {
        $.ajax({
            url: '/accounts/menucreate/',
            type: 'GET',
            beforeSend: function () {
                $('#menu_body').html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i></div>');
            },
            success: function (data) {
                $('#menu_body').html(data);

            },
            error: function (data) {
                $('#menu_body').html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i></div>');
            }
        })
    })
   
    $('#add-table').click(function () {
        $.ajax({
            url: '/accounts/tablecreate/',
            type: 'GET',
            beforeSend: function () {
                $('#table_body').html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i></div>');
            },
            success: function (data) {
                $('#table_body').html(data);
            },
            error: function (data) {
                $('#table_body').html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i></div>');
            }
        })
    })

    $('.update-menu').click(function () {
        var url = $(this).data('url');
        $.ajax({
            url: url,
            type: 'GET',
            beforeSend: function () {
                $('#menu_body').html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i></div>');
            },
            success: function (data) {
                $('#menu_body').html(data);
                $('#menu').modal('show');

            },
            error: function (data) {
                $('#menu_body').html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i></div>');
            }
        })
    })
    $(document).on('submit', '#menu_form', function (e) {
        e.preventDefault();
        $.ajax({
            url: $(this).attr("action"),
            type: "POST",
            data: new FormData(this),
            processData: false,
            contentType: false,
            success: function (data) {
                if (data.status == 'success') {
                    $("#menu").modal("hide");
                    location.reload();
                } else {
                    $('#menu_body').html(data);
                }
            }
        });
    });
    $('.update-table').click(function () {
        var url = $(this).data('url');
        $.ajax({
            url: url,
            type: 'GET',
            beforeSend: function () {
                $('#table_body').html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i></div>');
            },
            success: function (data) {
                $('#table_body').html(data);
                $('#table').modal('show');

            },
            error: function (data) {
                $('#table_body').html('<div class="text-center"><i class="fa fa-spinner fa-spin"></i></div>');
            }
        })
    })


    $(document).on('submit', '#table_form', function (e) {
        e.preventDefault();
        $.ajax({
            url: $(this).attr("action"),
            type: "POST",
            data: new FormData(this),
            processData: false,
            contentType: false,
            success: function (data) {
                if (data.status == 'success') {
                    $("#table").modal("hide");
                    location.reload();
                } else {
                    $('#table_body').html(data);
                }
            }
        });
    });
})
