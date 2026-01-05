
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

// Simulation parameters
const iterations = 1000;
const numDots = 2500; // Approx 1920x1080 / 30*30
const dots = [];
for (let i=0; i<numDots; i++) {
    dots.push({ x: Math.random() * 1920, y: Math.random() * 1080 });
}
const smoothMouse = { x: 960, y: 540 }; // Mouse in center

// Original function
function original() {
    let hits = 0;
    for (let i = 0; i < dots.length; i++) {
        const dot = dots[i];
        const dx = dot.x - smoothMouse.x;
        const dy = dot.y - smoothMouse.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < CONFIG.cursor.radius) {
            hits++;
            const cursorInfluence = Math.pow(1 - distance / CONFIG.cursor.radius, 2);
        }
    }
    return hits;
}

// Optimized function
// Precompute radiusSq
CONFIG.cursor.radiusSq = CONFIG.cursor.radius * CONFIG.cursor.radius;

function optimized() {
    let hits = 0;
    for (let i = 0; i < dots.length; i++) {
        const dot = dots[i];
        const dx = dot.x - smoothMouse.x;
        const dy = dot.y - smoothMouse.y;
        const distSq = dx * dx + dy * dy;

        if (distSq < CONFIG.cursor.radiusSq) {
            hits++;
            const distance = Math.sqrt(distSq);
            const cursorInfluence = Math.pow(1 - distance / CONFIG.cursor.radius, 2);
        }
    }
    return hits;
}

// Warmup
for (let i=0; i<100; i++) { original(); optimized(); }

// Measure Original
console.time('Original');
for (let i=0; i<iterations; i++) {
    original();
}
console.timeEnd('Original');

// Measure Optimized
console.time('Optimized');
for (let i=0; i<iterations; i++) {
    optimized();
}
console.timeEnd('Optimized');
