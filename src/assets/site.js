/* Selah Sound Collective — site shell behaviour (nav + library filter) */
(function () {
  var t = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  if (t && links) t.addEventListener('click', function () { links.classList.toggle('open'); });

  var grid = document.getElementById('libGrid');
  if (!grid) return;
  var cards = [].slice.call(grid.querySelectorAll('[data-title]'));
  var search = document.getElementById('libSearch');
  var chips = [].slice.call(document.querySelectorAll('.chip'));
  var empty = document.getElementById('libEmpty');
  var book = 'all';

  function apply() {
    var q = (search && search.value || '').trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (c) {
      var okBook = book === 'all' || c.getAttribute('data-book') === book;
      var okText = !q || c.getAttribute('data-title').toLowerCase().indexOf(q) !== -1;
      var show = okBook && okText;
      c.style.display = show ? '' : 'none';
      if (show) shown++;
    });
    if (empty) empty.style.display = shown ? 'none' : 'block';
  }
  if (search) search.addEventListener('input', apply);
  chips.forEach(function (ch) {
    ch.addEventListener('click', function () {
      chips.forEach(function (x) { x.classList.remove('on'); });
      ch.classList.add('on');
      book = ch.getAttribute('data-book');
      apply();
    });
  });
})();
