var socket = io();

socket.on('friend_added', function(data) {
    var html = `<li class="list-group-item d-flex flex-row justify-content-between friends-item border border-white"><span class="d-inline-flex mx-4" style="width: 100%; overflow: auto;">${data['email']}</span><button id="${data['email']}" class="btn btn-primary btn-sm" type="button" onclick="showMatches(this.id)">Show Matches</button></li>`;
    $('#friends-list').append(html);
});

socket.on('match_info', function(data) {
    $('#matching-user').text(data['email']);
    $('#match_count').text(data['count']);
});

socket.on('match', function(data) {
    var html = `<li class="list-group-item border border-white friends-item" style="width: 100%;"><a class="link-warning d-flex" href="${data['link']}" style="width: 100%;height: 100%;padding: 2px;"><span style="width: 100%;">${data['title']}</span></a></li>`;
    $('#matchlist').append(html);
});

function addFriend() {
    var email = $('#email-form').val();
    if (email.length != 0) {
        socket.emit('add_friend', {
            email: email
        });
    }
}

function showMatches(email) {
    $('#matchlist').empty();
    $('#matching-user').text('');
    $('#match_count').text('0');
    socket.emit('get_matches', {
        email: email
    });
}