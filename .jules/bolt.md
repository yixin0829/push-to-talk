## 2025-05-23 - [Canvas Batch Rendering]
**Learning:** HTML5 Canvas performance is heavily bound by the number of draw calls (overhead of communication between CPU and GPU). Even if the math is identical, batching thousands of `arc` + `fill` operations into a few grouped paths (by state, e.g., opacity) can reduce CPU overhead by 99%+.
**Action:** Always look for opportunities to batch similar Canvas operations. If state (color, opacity, line width) changes frequently, consider bucketing or sorting items by state before drawing.
