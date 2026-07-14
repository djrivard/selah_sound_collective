/* Selah Sound Collective — site shell behaviour (nav + two-tier library filter) */
(function () {
  var t = document.getElementById('navToggle');
  var links = document.getElementById('navLinks');
  if (t && links) t.addEventListener('click', function () { links.classList.toggle('open'); });

  var grid = document.getElementById('libGrid');
  if (!grid) return;
  var cards = [].slice.call(grid.querySelectorAll('[data-title]'));
  var search = document.getElementById('libSearch');
  var groupChips = [].slice.call(document.querySelectorAll('.chip[data-group]'));
  var bookRows = [].slice.call(document.querySelectorAll('.book-row'));
  var empty = document.getElementById('libEmpty');
  var hideBtn = document.getElementById('hideSoon');
  var group = 'all', book = null;
  var hideSoon = false;
  try { hideSoon = localStorage.getItem('selahHideSoon') === '1'; } catch (e) {}

  function apply() {
    var q = (search && search.value || '').trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (c) {
      var okGroup = group === 'all' || c.getAttribute('data-group') === group;
      var okBook = !book || c.getAttribute('data-book') === book;
      var okText = !q || c.getAttribute('data-title').toLowerCase().indexOf(q) !== -1;
      var okSoon = !hideSoon || !c.classList.contains('soon');
      var show = okGroup && okBook && okText && okSoon;
      c.style.display = show ? '' : 'none';
      if (show) shown++;
    });
    if (empty) empty.style.display = shown ? 'none' : 'block';
    if (hideBtn) {
      hideBtn.classList.toggle('on', hideSoon);
      hideBtn.setAttribute('aria-pressed', hideSoon ? 'true' : 'false');
      hideBtn.textContent = hideSoon ? 'Showing playable only' : 'Hide coming soon';
    }
  }

  if (hideBtn) hideBtn.addEventListener('click', function () {
    hideSoon = !hideSoon;
    try { localStorage.setItem('selahHideSoon', hideSoon ? '1' : '0'); } catch (e) {}
    apply();
  });

  function setGroup(g) {
    group = g; book = null;
    groupChips.forEach(function (x) { x.classList.toggle('on', x.getAttribute('data-group') === g); });
    bookRows.forEach(function (r) {
      var open = r.getAttribute('data-row') === g;
      r.classList.toggle('open', open);
      if (!open) [].forEach.call(r.querySelectorAll('.chip-book'), function (b) { b.classList.remove('on'); });
    });
    apply();
  }

  groupChips.forEach(function (ch) {
    ch.addEventListener('click', function () { setGroup(ch.getAttribute('data-group')); });
  });

  bookRows.forEach(function (r) {
    [].forEach.call(r.querySelectorAll('.chip-book'), function (b) {
      b.addEventListener('click', function () {
        var name = b.getAttribute('data-book');
        if (book === name) {          // tap again to clear back to the whole testament
          book = null; b.classList.remove('on');
        } else {
          book = name;
          [].forEach.call(r.querySelectorAll('.chip-book'), function (x) { x.classList.remove('on'); });
          b.classList.add('on');
        }
        apply();
      });
    });
  });

  if (search) search.addEventListener('input', apply);
  apply();
})();
