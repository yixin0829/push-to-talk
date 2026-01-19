/**
 * PushToTalk Landing Page - Animated Dot Grid
 * Creates flowing wave patterns using simplex noise
 */

(function() {
    'use strict';

    // ============================================
    // Simplex Noise Implementation
    // Based on Stefan Gustavson's implementation
    // ============================================

    class SimplexNoise {
        constructor(seed = Math.random()) {
            this.p = new Uint8Array(256);
            this.perm = new Uint8Array(512);
            this.permMod12 = new Uint8Array(512);

            // Initialize permutation array with seed
            for (let i = 0; i < 256; i++) {
                this.p[i] = i;
            }

            // Shuffle using seed
            let n, q;
            for (let i = 255; i > 0; i--) {
                seed = (seed * 16807) % 2147483647;
                n = seed % (i + 1);
                q = this.p[i];
                this.p[i] = this.p[n];
                this.p[n] = q;
            }

            for (let i = 0; i < 512; i++) {
                this.perm[i] = this.p[i & 255];
                this.permMod12[i] = this.perm[i] % 12;
            }
        }

        // Gradient vectors for 3D
        grad3 = [
            [1,1,0],[-1,1,0],[1,-1,0],[-1,-1,0],
            [1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1],
            [0,1,1],[0,-1,1],[0,1,-1],[0,-1,-1]
        ];

        dot3(g, x, y, z) {
            return g[0] * x + g[1] * y + g[2] * z;
        }

        noise3D(x, y, z) {
            const F3 = 1 / 3;
            const G3 = 1 / 6;

            let s = (x + y + z) * F3;
            let i = Math.floor(x + s);
            let j = Math.floor(y + s);
            let k = Math.floor(z + s);

            let t = (i + j + k) * G3;
            let X0 = i - t;
            let Y0 = j - t;
            let Z0 = k - t;
            let x0 = x - X0;
            let y0 = y - Y0;
            let z0 = z - Z0;

            let i1, j1, k1, i2, j2, k2;

            if (x0 >= y0) {
                if (y0 >= z0) { i1=1; j1=0; k1=0; i2=1; j2=1; k2=0; }
                else if (x0 >= z0) { i1=1; j1=0; k1=0; i2=1; j2=0; k2=1; }
                else { i1=0; j1=0; k1=1; i2=1; j2=0; k2=1; }
            } else {
                if (y0 < z0) { i1=0; j1=0; k1=1; i2=0; j2=1; k2=1; }
                else if (x0 < z0) { i1=0; j1=1; k1=0; i2=0; j2=1; k2=1; }
                else { i1=0; j1=1; k1=0; i2=1; j2=1; k2=0; }
            }

            let x1 = x0 - i1 + G3;
            let y1 = y0 - j1 + G3;
            let z1 = z0 - k1 + G3;
            let x2 = x0 - i2 + 2 * G3;
            let y2 = y0 - j2 + 2 * G3;
            let z2 = z0 - k2 + 2 * G3;
            let x3 = x0 - 1 + 3 * G3;
            let y3 = y0 - 1 + 3 * G3;
            let z3 = z0 - 1 + 3 * G3;

            let ii = i & 255;
            let jj = j & 255;
            let kk = k & 255;

            let gi0 = this.permMod12[ii + this.perm[jj + this.perm[kk]]];
            let gi1 = this.permMod12[ii + i1 + this.perm[jj + j1 + this.perm[kk + k1]]];
            let gi2 = this.permMod12[ii + i2 + this.perm[jj + j2 + this.perm[kk + k2]]];
            let gi3 = this.permMod12[ii + 1 + this.perm[jj + 1 + this.perm[kk + 1]]];

            let n0, n1, n2, n3;

            let t0 = 0.6 - x0*x0 - y0*y0 - z0*z0;
            if (t0 < 0) n0 = 0;
            else {
                t0 *= t0;
                n0 = t0 * t0 * this.dot3(this.grad3[gi0], x0, y0, z0);
            }

            let t1 = 0.6 - x1*x1 - y1*y1 - z1*z1;
            if (t1 < 0) n1 = 0;
            else {
                t1 *= t1;
                n1 = t1 * t1 * this.dot3(this.grad3[gi1], x1, y1, z1);
            }

            let t2 = 0.6 - x2*x2 - y2*y2 - z2*z2;
            if (t2 < 0) n2 = 0;
            else {
                t2 *= t2;
                n2 = t2 * t2 * this.dot3(this.grad3[gi2], x2, y2, z2);
            }

            let t3 = 0.6 - x3*x3 - y3*y3 - z3*z3;
            if (t3 < 0) n3 = 0;
            else {
                t3 *= t3;
                n3 = t3 * t3 * this.dot3(this.grad3[gi3], x3, y3, z3);
            }

            return 32 * (n0 + n1 + n2 + n3);
        }
    }

    // ============================================
    // Dot Grid Animation
    // ============================================

    const CONFIG = {
        dotSpacing: 30,        // Space between dots in pixels
        baseSize: 1.5,         // Base dot size
        maxSize: 5,            // Maximum dot size at wave peak
        noiseScale: 0.008,     // How "zoomed in" the noise is
        timeScale: 0.0003,     // Animation speed
        waveIntensity: 0.7,    // How strong the wave effect is
        baseOpacity: 0.05,     // Minimum opacity for dots
        maxOpacity: 0.3,       // Maximum opacity at wave peak
        color: { r: 255, g: 255, b: 255 },  // Dot color (white)

        // Cursor interaction settings
        cursor: {
            radius: 150,           // Radius of cursor influence (pixels)
            sizeMultiplier: 2.5,   // How much bigger dots get near cursor
            opacityMultiplier: 2,  // How much brighter dots get near cursor
            smoothing: 0.15        // Cursor position smoothing (0-1, lower = smoother)
        }
    };

    // Optimization: Batch rendering by opacity to reduce draw calls
    const BUCKET_COUNT = 50;
    const buckets = Array.from({ length: BUCKET_COUNT }, () => ({
        count: 0,
        xs: [], // Using simple arrays for flexibility
        ys: [],
        sizes: []
    }));

    // Pre-calculate colors for each bucket
    const bucketColors = Array.from({ length: BUCKET_COUNT }, (_, i) => {
        const opacity = i / (BUCKET_COUNT - 1);
        return `rgba(${CONFIG.color.r}, ${CONFIG.color.g}, ${CONFIG.color.b}, ${opacity})`;
    });

    let canvas, ctx;
    let noise;
    let dots = [];
    let animationId;
    let startTime;

    // Cursor tracking
    let mouse = { x: -1000, y: -1000 };       // Current mouse position (off-screen initially)
    let smoothMouse = { x: -1000, y: -1000 }; // Smoothed mouse position for fluid animation

    /**
     * Initialize the canvas and dots
     */
    function init() {
        canvas = document.getElementById('dot-grid-canvas');
        if (!canvas) return;

        ctx = canvas.getContext('2d');
        noise = new SimplexNoise(12345);
        startTime = performance.now();

        resize();
        window.addEventListener('resize', debounce(resize, 100));

        // Track mouse movement
        document.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        });

        // Move cursor off-screen when mouse leaves
        document.addEventListener('mouseleave', () => {
            mouse.x = -1000;
            mouse.y = -1000;
        });

        animate();
    }

    /**
     * Handle canvas resize
     */
    function resize() {
        const dpr = window.devicePixelRatio || 1;
        canvas.width = window.innerWidth * dpr;
        canvas.height = window.innerHeight * dpr;
        canvas.style.width = window.innerWidth + 'px';
        canvas.style.height = window.innerHeight + 'px';
        ctx.scale(dpr, dpr);

        // Regenerate dots grid
        createDots();
    }

    /**
     * Create the dot grid
     */
    function createDots() {
        dots = [];
        const cols = Math.ceil(window.innerWidth / CONFIG.dotSpacing) + 2;
        const rows = Math.ceil(window.innerHeight / CONFIG.dotSpacing) + 2;

        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                dots.push({
                    x: col * CONFIG.dotSpacing,
                    y: row * CONFIG.dotSpacing
                });
            }
        }
    }

    /**
     * Animation loop
     */
    function animate() {
        const time = (performance.now() - startTime) * CONFIG.timeScale;

        // Smooth cursor position for fluid animation
        smoothMouse.x += (mouse.x - smoothMouse.x) * CONFIG.cursor.smoothing;
        smoothMouse.y += (mouse.y - smoothMouse.y) * CONFIG.cursor.smoothing;

        ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);

        // Reset buckets
        for (let b = 0; b < BUCKET_COUNT; b++) {
            buckets[b].count = 0;
        }

        // 1. Calculate and bucket
        for (let i = 0; i < dots.length; i++) {
            const dot = dots[i];

            // Get noise value for this position and time
            const noiseValue = noise.noise3D(
                dot.x * CONFIG.noiseScale,
                dot.y * CONFIG.noiseScale,
                time
            );

            // Map noise (-1 to 1) to 0 to 1
            const normalizedNoise = (noiseValue + 1) / 2;

            // Calculate base dot properties from noise
            const intensity = Math.pow(normalizedNoise, 1.5) * CONFIG.waveIntensity;
            let size = CONFIG.baseSize + (CONFIG.maxSize - CONFIG.baseSize) * intensity;
            let opacity = CONFIG.baseOpacity + (CONFIG.maxOpacity - CONFIG.baseOpacity) * intensity;

            // Calculate cursor influence
            const dx = dot.x - smoothMouse.x;
            const dy = dot.y - smoothMouse.y;
            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < CONFIG.cursor.radius) {
                // Smooth falloff using cosine interpolation
                const cursorInfluence = Math.pow(1 - distance / CONFIG.cursor.radius, 2);

                // Amplify size and opacity near cursor
                size *= 1 + (CONFIG.cursor.sizeMultiplier - 1) * cursorInfluence;
                opacity = Math.min(1, opacity * (1 + (CONFIG.cursor.opacityMultiplier - 1) * cursorInfluence));
            }

            // Quantize opacity and add to bucket
            opacity = Math.max(0, Math.min(1, opacity));
            const bucketIdx = Math.floor(opacity * (BUCKET_COUNT - 1));
            const bucket = buckets[bucketIdx];

            // Expand arrays if needed (simple push)
            bucket.xs[bucket.count] = dot.x;
            bucket.ys[bucket.count] = dot.y;
            bucket.sizes[bucket.count] = size;
            bucket.count++;
        }

        // 2. Batch Draw
        for (let b = 0; b < BUCKET_COUNT; b++) {
            const bucket = buckets[b];
            if (bucket.count === 0) continue;

            // Skip invisible dots (bucket 0 is opacity 0)
            if (b === 0 && bucketColors[0].endsWith('0)')) continue;

            ctx.fillStyle = bucketColors[b];
            ctx.beginPath();

            for (let k = 0; k < bucket.count; k++) {
                const x = bucket.xs[k];
                const y = bucket.ys[k];
                const s = bucket.sizes[k];

                ctx.moveTo(x + s, y);
                ctx.arc(x, y, s, 0, Math.PI * 2);
            }

            ctx.fill();
        }

        animationId = requestAnimationFrame(animate);
    }

    /**
     * Debounce utility
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Fetch GitHub stars count
     */
    async function fetchGitHubStars() {
        const starsElement = document.getElementById('github-stars');
        if (!starsElement) return;

        try {
            const response = await fetch('https://api.github.com/repos/yixin0829/push-to-talk');
            if (response.ok) {
                const data = await response.json();
                const stars = data.stargazers_count;
                // Format: 1.2k for thousands
                starsElement.textContent = stars >= 1000
                    ? (stars / 1000).toFixed(1) + 'k'
                    : stars.toString();
            }
        } catch (error) {
            // Silently fail, keep the placeholder
            console.log('Could not fetch GitHub stars');
        }
    }

    /**
     * Initialize FAQ accordion
     */
    function initFAQ() {
        const faqItems = document.querySelectorAll('.faq-item');

        faqItems.forEach(item => {
            const question = item.querySelector('.faq-question');

            question.addEventListener('click', () => {
                const isActive = item.classList.contains('active');

                // Close all other items (accordion behavior)
                faqItems.forEach(otherItem => {
                    otherItem.classList.remove('active');
                    otherItem.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
                });

                // Toggle current item
                if (!isActive) {
                    item.classList.add('active');
                    question.setAttribute('aria-expanded', 'true');
                }
            });
        });
    }

    // ============================================
    // Mobile Menu
    // ============================================

    function initMobileMenu() {
        const menuBtn = document.getElementById('navbar-menu-btn');
        const mobileMenu = document.getElementById('mobile-menu');
        const overlay = document.getElementById('mobile-menu-overlay');
        const mobileLinks = mobileMenu.querySelectorAll('a');

        if (!menuBtn || !mobileMenu) return;

        function openMenu() {
            menuBtn.classList.add('active');
            menuBtn.setAttribute('aria-expanded', 'true');
            mobileMenu.classList.add('active');
            mobileMenu.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
        }

        function closeMenu() {
            menuBtn.classList.remove('active');
            menuBtn.setAttribute('aria-expanded', 'false');
            mobileMenu.classList.remove('active');
            mobileMenu.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        }

        menuBtn.addEventListener('click', () => {
            if (mobileMenu.classList.contains('active')) {
                closeMenu();
            } else {
                openMenu();
            }
        });

        // Close on overlay click
        overlay.addEventListener('click', closeMenu);

        // Close on link click
        mobileLinks.forEach(link => {
            link.addEventListener('click', closeMenu);
        });

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
                closeMenu();
            }
        });
    }

    // ============================================
    // Navbar Scroll Behavior
    // ============================================

    function initNavbarScroll() {
        const navbar = document.getElementById('navbar');
        if (!navbar) return;

        let lastScrollY = 0;
        let ticking = false;
        const hideThreshold = 300; // Pixels before hide/show kicks in

        function updateNavbar() {
            const currentScrollY = window.scrollY;

            // Hide/show navbar based on scroll direction
            if (currentScrollY > hideThreshold) {
                if (currentScrollY > lastScrollY && currentScrollY - lastScrollY > 10) {
                    // Scrolling down - hide navbar
                    navbar.classList.add('hidden');
                } else if (lastScrollY > currentScrollY && lastScrollY - currentScrollY > 10) {
                    // Scrolling up - show navbar
                    navbar.classList.remove('hidden');
                }
            } else {
                navbar.classList.remove('hidden');
            }

            lastScrollY = currentScrollY;
            ticking = false;
        }

        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateNavbar);
                ticking = true;
            }
        }, { passive: true });

        // Initial call
        updateNavbar();
    }

    // ============================================
    // Scroll Spy - Active Section Highlighting
    // ============================================

    function initScrollSpy() {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('.navbar-links a[data-section], .mobile-menu-links a[data-section]');

        if (sections.length === 0 || navLinks.length === 0) return;

        function updateActiveLink() {
            const scrollY = window.scrollY;
            const windowHeight = window.innerHeight;

            let currentSection = '';

            sections.forEach(section => {
                const sectionTop = section.offsetTop - 150;
                const sectionHeight = section.offsetHeight;

                if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
                    currentSection = section.getAttribute('id');
                }
            });

            // If near top of page, no section is active
            if (scrollY < 300) {
                currentSection = '';
            }

            // If near bottom, activate FAQ
            if ((window.innerHeight + window.scrollY) >= document.documentElement.scrollHeight - 100) {
                currentSection = 'faq';
            }

            navLinks.forEach(link => {
                const linkSection = link.getAttribute('data-section');
                if (linkSection === currentSection) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        }

        window.addEventListener('scroll', debounce(updateActiveLink, 50), { passive: true });
        updateActiveLink();
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            init();
            fetchGitHubStars();
            initFAQ();
            initMobileMenu();
            initNavbarScroll();
            initScrollSpy();
        });
    } else {
        init();
        fetchGitHubStars();
        initFAQ();
        initMobileMenu();
        initNavbarScroll();
        initScrollSpy();
    }
})();
