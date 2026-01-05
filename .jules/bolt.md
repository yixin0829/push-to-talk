## 2024-05-23 - Avoid Math.sqrt in Animation Loops
**Learning:** `Math.sqrt` is computationally expensive in tight loops (like `requestAnimationFrame`). For distance checks, comparing squared distance (`dx*dx + dy*dy`) against squared radius is significantly faster (~6x in micro-benchmarks) and mathematically equivalent.
**Action:** Always use squared distance checks for proximity detection in animation loops or collision detection. Only calculate actual square root when the scalar distance is strictly needed (e.g., for interpolation).
