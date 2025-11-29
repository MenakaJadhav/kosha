// coach/static/coach/coach.js
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.js-mark-read').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      // use fetch to submit
      const cardId = formData.get('card_id');
      try {
        const res = await fetch(form.action, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: formData
        });
        if (res.ok) {
          // mark UI as read
          form.style.display = 'none';
          const parent = form.closest('article');
          if (parent) {
            const span = document.createElement('span');
            span.className = 'muted';
            span.innerText = 'Read';
            parent.querySelector('.card-head')?.appendChild(span);
          }
        }
      } catch (err) {
        console.error(err);
      }
    });
  });
});

// simple CSRF helper
function getCookie(name) {
  const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return v ? v.pop() : '';
}
