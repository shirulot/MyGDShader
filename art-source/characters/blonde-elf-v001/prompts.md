# 金发妖精剑士：生成提示词

生成方式：内置 image_gen。日期：2026-10-13。

第一张为原创角色，后续以我们生成的角色图作一致性参考。

## 角色初稿

```text
Use case: stylized-concept.
Asset type: original pixel-art action RPG character, eight-direction standing sprite study, transparent PNG.
Create an original beautiful adult blonde elf swordswoman for a 2D oblique top-down fantasy action RPG. She has long clearly pointed ears, honey-gold hair in a high flowing ponytail with two face-framing locks, green eyes, a small emerald hair tie, a fitted forest-green sleeveless combat tunic with ivory undershirt, short split tunic tails over dark fitted shorts, brown belt, brown forearm guards and knee-high boots, modest restrained brass clasps. Graceful athletic proportions about 5 heads tall, elegant readable face, not a chibi or oversized head. Holds one simple silver straight sword in her RIGHT hand, pointed down at rest.
Style: crisp professional hand-pixeled Japanese fantasy action-game sprites. Strong dark selective outlines, purposeful chunky pixel clusters, 3-tone stepped shading per material, compact palette, clear negative spaces between limbs, clean silhouettes, visually about 64–72 source pixels in character height shown at an integer enlarged scale. Clean and economical sprites, not detailed painted illustrations with a pixel filter. No smooth gradients, blur, glossy 3D, or antialiasing.
Camera: consistent orthographic oblique top-down view, camera looking down roughly 35 degrees from the ground plane; clearly see the top of the head and shoulders in ALL eight directions. The front-facing pose still shows a little top of the head and both feet. This is not a side-scroller, not a portrait turntable, not overhead-only.
Layout: EXACTLY eight isolated full-body standing sprites arranged in four equal columns and two equal rows on a 3:2 landscape canvas, generous transparent spacing, equal character scale and foot baseline within each row. In reading order: row 1 SOUTH (front), SOUTHWEST (front-left three-quarter, face points image-left), WEST (left profile viewed from above), NORTHWEST (back-left three-quarter); row 2 NORTH (back), NORTHEAST (back-right three-quarter), EAST (right profile viewed from above), SOUTHEAST (front-right three-quarter). These are eight ROTATIONS of the same character, not different designs. Keep identical hair tie, ponytail, outfit, limb proportions and sword throughout; correct anatomical right-handed sword even in back views. Calm combat-ready idle stance. Each whole sword and every strand silhouette fit inside its own cell.
Background: actual transparent alpha, no checkerboard drawing, no floor, no cast shadow, no scene. No wings. No text, labels, numbers, frames, borders or watermarks.
```

## 八方向像素修订

```text
Use case: style-transfer. Input image is our original blonde elf character design reference. Redraw the exact same character as MUCH LOWER RESOLUTION GAME PIXEL ART, maintaining the eight direction order and the top-down camera. This is a deliberate major simplification from illustration into tiny sprite art.
CRITICAL STYLE: each individual character is only about 56 pixels tall on a native 384x256 pixel sheet, then that entire sheet is enlarged exactly 4x with nearest-neighbor to 1536x1024. Thus every source pixel is a clearly visible solid 4x4 square. Draw as though in Aseprite with a one-pixel pencil at the native size. Use only 24 solid colors for the entire character. 2 or 3 flat tones per material. Hair is 3 or 4 broad yellow clusters, not individually rendered strands. Face has a few deliberate pixels for eyes, no detailed rendered face. NO fine texture, tiny hatching, gradient, smooth outlines or illustration rendering.
Adult beautiful blonde elf swordswoman, long pointed ears, high golden ponytail with green tie, green split tunic over dark shorts, ivory shirt accents, brown gloves and boots, straight silver sword in anatomical right hand. Elegant athletic 5-head proportions, not chibi.
EXACTLY 8 sprites, 4 columns by 2 rows. Row 1 front/SOUTH, front-left/SOUTHWEST, left/WEST, back-left/NORTHWEST. Row 2 back/NORTH, back-right/NORTHEAST, right/EAST, front-right/SOUTHEAST. Constant oblique overhead camera at 35 degrees downward, showing head tops and upper shoulder surfaces in every view. Same scale and pixel grid across all eight, generous empty gutters, full weapons inside cells, no overlaps.
Only the 8 sprite silhouettes have opacity. The entire background must be completely empty TRANSPARENT alpha=0, including all space between sprites. No colored fog or gradient halo, no ground shadows, no floor, no checkerboard. No text.
```

## 东南向走路

```text
Use case: identity-preserve. Asset type: pixel-art game animation sprite sheet. The input image is our original character design reference. Preserve EXACTLY this same adult blonde elf heroine: pointed ears, high golden ponytail with green tie, green split tunic with ivory accents, dark fitted shorts, brown forearm guards and boots, silver sword in her anatomical RIGHT hand. Same face, hair, proportions and colors.
Render genuine economical game pixel art: large crisp square pixel clusters, limited 24-color palette, 2–3 solid shading steps per material, no painted texture or individual hair strands. About 64 logical source pixels in character height, integer enlarged so pixels are visible. Graceful athletic adult proportions around 5 heads tall, not chibi.
Camera must be a FIXED orthographic oblique top-down view looking down 35 degrees, with top of head and shoulder surfaces visible. All frames face SOUTHEAST (front-right three-quarter, face points diagonally toward image bottom-right), never change facing or camera.
Composition: 1536x1024 landscape transparent sprite sheet, EXACTLY 8 equal cells in 4 columns by 2 rows, reading order left to right then next row. Same scale, same ground anchor coordinate within every cell, wide empty gutters, no sprite or sword extends outside its own cell. All eight frames show the full body. No drawn grid or labels.
Only character and sword pixels are opaque; completely empty transparent alpha background, no atmospheric backdrop, no floor, no cast shadows, no glow or gradient halos. No text, numbering, watermark or interface.
ACTION: a coherent in-place WALK CYCLE, eight successive animation frames for a full left-and-right step. This is animation of ONE fixed direction, NOT a turnaround. Frame 1 right foot contact forward, left foot back; 2 down/recoil on right foot; 3 left foot passing right foot; 4 left leg lifting and swinging forward; 5 left foot contact forward, right foot back; 6 down/recoil on left foot; 7 right foot passing left foot; 8 right leg lifting and swinging forward to loop into frame 1. Keep pelvis position stable, subtle vertical bob, arms counter-swing naturally. Sword is held low safely in right hand, no swinging attack. Ponytail and tunic tails lag behind body motion. Make opposite contact poses in frames 1 and 5 clearly distinct, feet must alternate, do not repeat the same pose eight times.
```

## 东南向挥剑

```text
Use case: identity-preserve. Asset type: pixel-art game animation sprite sheet. The input image is our original character design reference. Preserve EXACTLY this same adult blonde elf heroine: pointed ears, high golden ponytail with green tie, green split tunic with ivory accents, dark fitted shorts, brown forearm guards and boots, silver sword in her anatomical RIGHT hand. Same face, hair, proportions and colors.
Render genuine economical game pixel art: large crisp square pixel clusters, limited 24-color palette, 2–3 solid shading steps per material, no painted texture or individual hair strands. About 64 logical source pixels in character height, integer enlarged so pixels are visible. Graceful athletic adult proportions around 5 heads tall, not chibi.
Camera must be a FIXED orthographic oblique top-down view looking down 35 degrees, with top of head and shoulder surfaces visible. All frames face SOUTHEAST (front-right three-quarter, face points diagonally toward image bottom-right), never change facing or camera.
Composition: 1536x1024 landscape transparent sprite sheet, EXACTLY 8 equal cells in 4 columns by 2 rows, reading order left to right then next row. Same scale, same ground anchor coordinate within every cell, wide empty gutters, no sprite or sword extends outside its own cell. All eight frames show the full body. No drawn grid or labels.
Only character and sword pixels are opaque; completely empty transparent alpha background, no atmospheric backdrop, no floor, no cast shadows, no glow or gradient halos. No text, numbering, watermark or interface.
ACTION: one powerful right-handed SWORD SLASH in eight successive key animation frames, all aimed southeast. Translate the dynamic body mechanics of a hand-drawn side-scrolling action game into this oblique top-down camera. 1 combat-ready guard, 2 weight lowers and hips coil, 3 full anticipation with sword pulled back above right shoulder and ponytail trailing, 4 explosive diagonal forward slash with extended arm and planted lead foot, 5 lowest and widest follow-through with sword sweeping across the front and torso rotating, 6 deceleration with hair catching up, 7 returning sword to guard, 8 recovered neutral matching first pose. Strong shoulder/hip rotation, readable silhouette changes, right hand firmly grips sword throughout, constant blade length. The sword itself should stay visible; a small sharp pale mint crescent immediately alongside the blade only in frames 4 and 5 is allowed, but no oversized VFX hiding the anatomy. Keep overall facing southeast throughout; torso rotates naturally as part of strike. No flips, no aerial poses, no extra weapons.
```

