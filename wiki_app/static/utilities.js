function search_if_necessary(e) {
    if(e.keyCode === 13) {
        window.location.href = "/wiki_page/search?text=" + document.getElementById('search_box').value;
    }
}