# WDC 2026 Eight Concepts — Visual QA

## Selected candidate set

| No. | Asset | Diabolo geometry | Logo-safe left | Taiwan signal | Notes |
| --- | --- | --- | --- | --- | --- |
| 01 | `01-taipei-neon-night.webp` | Clear, symmetric, realistic | Strong | Taipei 101 / night skyline | Closest to the current direction; practical default candidate. |
| 02 | `02-temple-lantern-glow.webp` | Clear, symmetric perspective | Strong | Temple roof / lanterns | Strongest traditional Taiwan identity. |
| 03 | `03-jiufen-rain.webp` | Clear, dynamic perspective | Strong | Jiufen hillside / rain / lanterns | Strong atmosphere and story; slightly softer at small size. |
| 04 | `04-sun-moon-lake-dawn.webp` | Plausible three-quarter view | Good | Lake / pavilion / mountain mist | Calmest and most refined; less explicitly sports-oriented. |
| 05 | `05-alishan-sunrise.webp` | Clear, symmetric, realistic | Strong | Alishan / cloud sea / heritage train | Strongest uplifting competition energy. |
| 06 | `06-taiwan-retro-print.webp` | Clean intentional graphic form | Strong | Taipei 101 / temple / mountains | Most distinctive graphic concept; deliberately non-photorealistic. |
| 07 | `07-future-taipei-circuit.webp` | Clear, symmetric, realistic | Strong | Taipei 101 / luminous city routes | Strong speed and international-event character. |
| 08 | `08-paper-cut-ink-taiwan-v3.webp` | Corrected, clear three-quarter form | Strong | Temple / blossoms / lanterns / ink mountains | Final v3 selected after axle and viewing-angle corrections. |

## Shared checks

- Exactly one diabolo appears in every selected candidate.
- No generated lettering, false logos, flags, people, hands, sponsor marks, or watermarks were found.
- All selected images are 1672x941 WebP files and preserve a 16:9 source ratio.
- The supplied full WDC logo and mark logo remain separate HTML overlays in the preview; generated images do not imitate the official logo.
- Desktop hero and PICK UP compositions keep the logo and diabolo separated.

## Mobile finding

The current production mobile hero uses a 375x390-style vertical frame with `object-fit: cover`. A centered crop of a shared 16:9 image naturally trims part of the right-side diabolo in most concepts. The comparison page deliberately shows this as `MOBILE HERO — CURRENT CROP`.

This is a responsive-layout decision, not a defect in the 16:9 candidate files. After a candidate is selected, keep the same image file and choose one mobile treatment: `object-fit: contain` on a dark field, or a selected `object-position`/scale compromise. No production CSS has been changed during this concept run.

## Retained drafts

- `08-paper-cut-ink-taiwan.webp`: first paper-cut draft; symmetric but can read as a bow at card size.
- `08-paper-cut-ink-taiwan-v2.webp`: clearer axle, still frontal.
- `08-paper-cut-ink-taiwan-v3.webp`: selected three-quarter form.
