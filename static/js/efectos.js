/* Efectos inspirados en React Bits, escritos en JavaScript puro
   para usarlos directamente en los templates de Django. */
(function () {
    'use strict';

    var sinMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // data-d="3" → retraso escalonado de la animación de entrada (sin estilos inline, por la CSP).
    document.querySelectorAll('[data-d]').forEach(function (el) {
        el.style.setProperty('--d', el.dataset.d);
    });

    // BlurText: divide el texto en palabras que aparecen desde el desenfoque.
    document.querySelectorAll('[data-blur-text]').forEach(function (el) {
        var palabras = el.textContent.trim().split(/\s+/);
        el.setAttribute('aria-label', el.textContent.trim());
        el.textContent = '';
        palabras.forEach(function (palabra, i) {
            var span = document.createElement('span');
            span.className = 'blur-word';
            span.style.setProperty('--i', i);
            span.setAttribute('aria-hidden', 'true');
            span.textContent = palabra;
            el.appendChild(span);
            el.appendChild(document.createTextNode(' '));
        });
    });

    // SpotlightCard: la luz sigue al cursor dentro de la tarjeta.
    document.querySelectorAll('.spotlight').forEach(function (card) {
        card.addEventListener('pointermove', function (e) {
            var r = card.getBoundingClientRect();
            card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
            card.style.setProperty('--my', (e.clientY - r.top) + 'px');
        });
    });

    // CountUp: anima los números cuando entran en pantalla.
    function contar(el) {
        var fin = parseInt(el.dataset.countUp, 10) || 0;
        if (sinMovimiento || fin === 0) {
            el.textContent = fin.toLocaleString('es-CL');
            return;
        }
        var inicio = null;
        var duracion = 1400;
        function paso(t) {
            if (!inicio) inicio = t;
            var p = Math.min((t - inicio) / duracion, 1);
            var suave = 1 - Math.pow(1 - p, 3);
            el.textContent = Math.round(fin * suave).toLocaleString('es-CL');
            if (p < 1) requestAnimationFrame(paso);
        }
        requestAnimationFrame(paso);
    }

    // Reveal (AnimatedContent) + CountUp con IntersectionObserver.
    var observados = document.querySelectorAll('.reveal, [data-count-up]');
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entradas) {
            entradas.forEach(function (entrada) {
                if (!entrada.isIntersecting) return;
                var el = entrada.target;
                if (el.hasAttribute('data-count-up')) contar(el);
                else el.classList.add('visible');
                io.unobserve(el);
            });
        }, { threshold: 0.15 });
        observados.forEach(function (el) { io.observe(el); });
    } else {
        observados.forEach(function (el) {
            if (el.hasAttribute('data-count-up')) contar(el);
            else el.classList.add('visible');
        });
    }

    // Respaldo: si algo no llegó a animarse, se muestra igual.
    setTimeout(function () {
        document.querySelectorAll('.reveal').forEach(function (el) { el.classList.add('visible'); });
    }, 2500);

    // Toasts: se cierran solos después de unos segundos.
    document.querySelectorAll('.toast-msg').forEach(function (toast, i) {
        function cerrar() {
            toast.classList.add('saliendo');
            setTimeout(function () { toast.remove(); }, 320);
        }
        toast.querySelector('button').addEventListener('click', cerrar);
        setTimeout(cerrar, 4500 + i * 400);
    });

    // ClickSpark: chispas al hacer clic en cualquier parte.
    if (sinMovimiento) return;
    var canvas = document.createElement('canvas');
    canvas.className = 'click-spark';
    document.body.appendChild(canvas);
    var ctx = canvas.getContext('2d');
    var chispas = [];
    var animando = false;

    function ajustar() {
        var dpr = window.devicePixelRatio || 1;
        canvas.width = window.innerWidth * dpr;
        canvas.height = window.innerHeight * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    ajustar();
    window.addEventListener('resize', ajustar);

    function dibujar(t) {
        ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
        chispas = chispas.filter(function (c) {
            var p = (t - c.inicio) / 420;
            if (p >= 1) return false;
            var suave = p * (2 - p);
            var dist = suave * 26;
            var largo = 9 * (1 - suave);
            var x1 = c.x + dist * Math.cos(c.angulo);
            var y1 = c.y + dist * Math.sin(c.angulo);
            ctx.strokeStyle = c.color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x1 + largo * Math.cos(c.angulo), y1 + largo * Math.sin(c.angulo));
            ctx.stroke();
            return true;
        });
        if (chispas.length) requestAnimationFrame(dibujar);
        else animando = false;
    }

    document.addEventListener('click', function (e) {
        var ahora = performance.now();
        var colores = ['#2dd4bf', '#f5c76b', '#ff7a5c'];
        for (var i = 0; i < 8; i++) {
            chispas.push({
                x: e.clientX,
                y: e.clientY,
                angulo: (Math.PI * 2 * i) / 8,
                inicio: ahora,
                color: colores[i % colores.length]
            });
        }
        if (!animando) {
            animando = true;
            requestAnimationFrame(dibujar);
        }
    });
})();
