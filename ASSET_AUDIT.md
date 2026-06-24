# PZ Crossbows Asset Audit

Date: 2026-06-24

## Purpose

This audit tracks every non-code asset currently shipped or staged for the Project Zomboid `PZCrossbows` mod. The release goal is a Steam Workshop-safe build with no copied assets from old mods, Rust, or any other source without explicit permission.

Conservative rule for this project: if an asset was copied, derived from a copied asset, or has unclear origin, treat it as `REPLACE BEFORE PUBLIC RELEASE`.

## Summary

| Area | Count | Current release status | Notes |
|---|---:|---|---|
| Workshop images | 2 | Replace | `preview.png` and `poster.png` are identical hashes. |
| Root mod icon copy | 1 | Replace or remove duplicate | `42/Item_CrossBowDrawn.png` duplicates `media/textures/Item_CrossBowDrawn.png`. |
| Item icons | 17 | Replace | Includes crossbows, bolts, shafts, and bolt head icons. |
| Model textures | 3 | Replace | Crossbow, compound crossbow, and wood bolt textures. |
| 3D models | 11 | Candidate replacement | Generated low-poly Blender models are now installed in `media/models_x`; verify in game before marking final. |
| Shipped sounds | 9 | Replace | All current `.ogg` files should be replaced with original or licensed audio. |
| Staged Rust audio | 1 | Do not ship | `needed files/2021CrossbowRust.ogg` is outside the mod and untracked. |

## Release Policy

Before public Steam Workshop upload:

- Remove or replace every asset marked `Replace`.
- Do not include `needed files/2021CrossbowRust.ogg` or any Rust-derived cuts in the public release.
- Keep source/license notes for every replacement asset.
- If using AI-generated, recorded, CC0, or commissioned assets, document the source in this file.
- Keep filenames stable when possible so scripts do not need asset path rewrites.

## Workshop And Mod UI Images

| File | Size | Status | Action |
|---|---:|---|---|
| `PZCrossbows/preview.png` | 256x256, 80068 bytes | Replace | Make original Workshop preview image. |
| `PZCrossbows/Contents/mods/PZCrossbows/42/poster.png` | 256x256, 80068 bytes | Replace | Can reuse final preview if it is original. |
| `PZCrossbows/Contents/mods/PZCrossbows/42/Item_CrossBowDrawn.png` | 32x32, 660 bytes | Replace or remove duplicate | Used by `mod.info` as icon. Duplicate of item icon hash. |

`preview.png` and `poster.png` have the same SHA-256 hash. That is not a technical issue, but both still need an owned final image.

## Item Icons

All item icons are currently treated as copied or unclear-origin development assets. Replace before release.

| File | Size | Used by | Status | Replacement note |
|---|---:|---|---|---|
| `media/textures/Item_CrossBow.png` | 32x32, 658 bytes | `Icon = CrossBow` | Replace | Crude crossbow inventory icon. |
| `media/textures/Item_CrossBowDrawn.png` | 32x32, 660 bytes | Lua drawn state, mod icon duplicate | Replace | Loaded crude crossbow icon. |
| `media/textures/Item_ImprovedCrossBow.png` | 32x32, 721 bytes | `Icon = ImprovedCrossBow` | Replace | Improved crossbow icon. |
| `media/textures/Item_ImprovedCrossBowDrawn.png` | 32x32, 652 bytes | Lua drawn state | Replace | Loaded improved crossbow icon. |
| `media/textures/Item_CompoundCrossBow.png` | 32x32, 848 bytes | `Icon = CompoundCrossBow` | Replace | Compound crossbow icon. |
| `media/textures/Item_CompoundCrossBowDrawn.png` | 32x32, 791 bytes | Lua drawn state | Replace | Loaded compound crossbow icon. |
| `media/textures/Item_HandCrossBow.png` | 32x32, 582 bytes | `Icon = HandCrossBow` | Replace | Hand crossbow icon. |
| `media/textures/Item_HandCrossBowDrawn.png` | 32x32, 621 bytes | Lua loaded state | Replace | Loaded hand crossbow icon. |
| `media/textures/Item_WoodBolt.png` | 32x32, 340 bytes | `Icon = WoodBolt` | Replace | Full-length wood bolt icon. |
| `media/textures/Item_BrokenWoodBolt.png` | 32x32, 435 bytes | `Icon = BrokenWoodBolt` | Replace | Broken full-length bolt icon. |
| `media/textures/Item_WoodBoltShaft.png` | 32x32, 282 bytes | `Icon = WoodBoltShaft` | Replace | Full-length shaft icon. |
| `media/textures/Item_ShortWoodBolt.png` | 32x32, 315 bytes | `Icon = ShortWoodBolt` | Replace | Short bolt icon. |
| `media/textures/Item_ShortBrokenWoodBolt.png` | 32x32, 342 bytes | `Icon = ShortBrokenWoodBolt` | Replace | Broken short bolt icon. |
| `media/textures/Item_ShortWoodBoltShaft.png` | 32x32, 243 bytes | `Icon = ShortWoodBoltShaft` | Replace | Short shaft icon. |
| `media/textures/Item_StoneBoltHead.png` | 32x32, 676 bytes | `Icon = StoneBoltHead` | Replace or verify | If copied from vanilla/reference mod, replace. If vanilla-derived is not allowed, redraw. |

## Model Textures

| File | Size | Used by | Status | Action |
|---|---:|---|---|---|
| `media/textures/weapons/firearm/CrossBow.png` | 1024x1024, 42611 bytes | Crossbow, improved, hand models | Candidate replacement | Generated opaque placeholder texture for visibility testing. |
| `media/textures/weapons/firearm/CompoundCrossBow.png` | 512x512, 10772 bytes | Compound crossbow models | Candidate replacement | Generated opaque placeholder texture for visibility testing. |
| `media/textures/weapons/firearm/WoodBolt.png` | 1024x1024, 42614 bytes | Wood bolt models | Candidate replacement | Generated opaque placeholder texture for visibility testing. |

## 3D Models

The old copied `.fbx` models have been replaced in `media/models_x` with generated low-poly Blender models from `blender/generate_original_models.py`. The generated meshes are fitted into the old FBX coordinate/bounding-box space by `blender/fit_models_to_reference_space.py` so the existing model script scale and attachments can be tested without reauthoring every offset.

| File | Bytes | Used by model script | Status | Action |
|---|---:|---|---|---|
| `media/models_x/weapons/firearm/CrossBow.fbx` | 33404 | `model CrossBow` | Candidate replacement | Generated single-mesh crude crossbow model, fitted to old coordinate space. |
| `media/models_x/weapons/firearm/CrossBowDrawn.fbx` | 37276 | `model CrossBowDrawn` | Candidate replacement | Generated single-mesh loaded crude crossbow model, fitted to old coordinate space. |
| `media/models_x/weapons/firearm/ImprovedCrossBow.fbx` | 32108 | `model ImprovedCrossBow` | Candidate replacement | Generated single-mesh improved crossbow model, fitted to old coordinate space. |
| `media/models_x/weapons/firearm/ImprovedCrossBowDrawn.fbx` | 35068 | `model ImprovedCrossBowDrawn` | Candidate replacement | Generated single-mesh loaded improved crossbow model, fitted to old coordinate space. |
| `media/models_x/weapons/firearm/CompoundCrossBow.fbx` | 39548 | `model CompoundCrossBow` | Candidate replacement | Generated single-mesh compound crossbow model, fitted to old coordinate space. |
| `media/models_x/weapons/firearm/CompoundCrossBowDrawn.fbx` | 43788 | `model CompoundCrossBowDrawn` | Candidate replacement | Generated single-mesh loaded compound crossbow model, fitted to old coordinate space. |
| `media/models_x/weapons/firearm/HandCrossBow.fbx` | 29932 | `model HandCrossBow` | Candidate replacement | Generated single-mesh hand crossbow model, fitted to old coordinate space. |
| `media/models_x/weapons/firearm/HandCrossBowDrawn.fbx` | 33916 | `model HandCrossBowDrawn` | Candidate replacement | Generated single-mesh loaded hand crossbow model, fitted to old coordinate space. |
| `media/models_x/weapons/firearm/WoodBolt.fbx` | 22860 | `model WoodBolt` | Candidate replacement | Generated single-mesh full-length bolt model, fitted to old coordinate space. |
| `media/models_x/weapons/firearm/ShortWoodBolt.fbx` | 22956 | `model ShortWoodBolt` | Candidate replacement | Generated single-mesh short bolt model, fitted to old coordinate space. |
| `media/models_x/weapons/firearm/WoodBoltBroken.fbx` | 21276 | `model WoodBoltBroken` | Candidate replacement | Generated single-mesh broken bolt model, fitted to old coordinate space. |

## Shipped Sounds

All currently shipped `.ogg` files are treated as copied or unclear-origin development assets. Replace before public release.

Audio duration could not be measured in this environment because `ffprobe` is not installed. Byte sizes are recorded for tracking.

| File | Bytes | Script usage | Status | Replacement note |
|---|---:|---|---|---|
| `media/sound/CrossbowShoot.ogg` | 10697 | `SwingSound = CrossbowShoot` | Replace | Main crude/improved/hand shot. |
| `media/sound/CompoundCrossBowShoot.ogg` | 16792 | `SwingSound = CompoundCrossBowShoot` | Candidate replacement | Generated Firefly WAV converted to OGG/Vorbis, trimmed to 0.828s, normalized with headroom. Verify license before Workshop release. |
| `media/sound/CrossbowDryShot.ogg` | 5532 | `ClickSound = CrossbowDryShot` | Replace | Empty trigger/dry shot. |
| `media/sound/CrossbowHitBlood.ogg` | 16297 | `ImpactSound = CrossbowHitBlood` | Replace | Bolt impact on character/zombie. |
| `media/sound/CrossbowReload.ogg` | 15561 | No direct script reference found | Remove or map intentionally | Current scripts use `CrossbowReloadStop` for insert/eject/rack. |
| `media/sound/CrossbowReloadStart.ogg` | 26113 | No direct script reference found | Remove or map intentionally | Not currently referenced. |
| `media/sound/CrossbowReloadStop.ogg` | 26113 | Insert/eject/rack for non-compound crossbows | Replace | Generic reload/rack sound. |
| `media/sound/CompoundCrossBowReload.ogg` | 17492 | Insert/eject for compound crossbow | Replace | Compound reload sound. |
| `media/sound/CompoundCrossBowRack.ogg` | 17109 | Rack for compound crossbow | Replace | Compound rack sound. |

### Missing Or External Sound Event

`PZCrossbows_crossbowsTwine.txt` references `BreakSound = HandCrossbowBreak`, but no `media/sound/HandCrossbowBreak.ogg` exists in this mod.

Action: verify whether `HandCrossbowBreak` is a valid vanilla sound event in Build 42.19. If not, replace the script value with a shipped original sound event/file.

## Staged External Audio

| File | Bytes | Git status | Status | Action |
|---|---:|---|---|---|
| `needed files/2021CrossbowRust.ogg` (`potribni fayly/2021CrossbowRust.ogg` on disk) | unknown in audit table, SHA tracked below | Untracked | Do not ship | Rust-derived audio should not be included in Workshop release unless licensed. Use only for private reference. |

The actual directory name on disk is Ukrainian: `потрібні файли/2021CrossbowRust.ogg`. It is currently outside the mod package and untracked by git.

## Code And Data Notes

This audit focuses on media assets. Code still deserves a separate provenance review if old mod Lua was copied line-for-line.

Current code-level release concerns found while auditing:

- `media/lua/server/zPZCrossbowsClient.lua` contains client-side UI/model/reload patches despite being under `server`.
- `workshop.txt` and `mod.info` still mention metal bolts, but the current item set only includes wood and short wood bolts.

## Replacement Plan

Recommended order:

1. Replace or remove all shipped sounds first, keeping the same event filenames where practical.
2. Replace `preview.png`, `poster.png`, and the mod icon with simple original artwork.
3. Replace 32x32 item icons with original icons; this can be done before final 3D models.
4. Replace model textures.
5. Replace `.fbx` models and then retune model attachments in `PZCrossbows_models.txt`.
6. Remove unused leftover assets after a final reference scan.
7. Update this audit with `Source`, `License`, and `Date replaced` for each asset.

## SHA-256 Tracking

Hashes are useful for proving that old assets were actually removed in later commits.

| SHA-256 | File |
|---|---|
| `8BEE876DB5B2DE46808E51D12B2F77C5B04D4471E59AD593C3D107A4B2EC9E3C` | `PZCrossbows/preview.png` |
| `8BEE876DB5B2DE46808E51D12B2F77C5B04D4471E59AD593C3D107A4B2EC9E3C` | `PZCrossbows/Contents/mods/PZCrossbows/42/poster.png` |
| `31D620D3E6DE8A7DF8CC229E43A973F000768778B7F5F5F0B2D847EA515C60FC` | `PZCrossbows/Contents/mods/PZCrossbows/42/Item_CrossBowDrawn.png` |
| `31D620D3E6DE8A7DF8CC229E43A973F000768778B7F5F5F0B2D847EA515C60FC` | `media/textures/Item_CrossBowDrawn.png` |
| `99EA3ACA253B36E13D4B8C88D3FD4CFF80FDE9C9EA074B38B6FA0873C03AB4BF` | `media/textures/Item_CrossBow.png` |
| `54852A5BF746C2AC5A4771F418F61A3722DA6E614CCCA004DD7E1A7789ED238A` | `media/textures/Item_ImprovedCrossBow.png` |
| `60A77B5212758D80303C5725CF0C018EFE45138441E5446180EFDEF8F8D25E66` | `media/textures/Item_ImprovedCrossBowDrawn.png` |
| `9DBE4340F95F6AE2DDC7AC45A2072A3E69602EB5D63167D468CB887483FCDE87` | `media/textures/Item_CompoundCrossBow.png` |
| `58E3B62970982007AFF765443085199FDBBFBD2EE430956CA26FA4307EB09428` | `media/textures/Item_CompoundCrossBowDrawn.png` |
| `9B818D69E29BF514B1803F32834C8C7719426722DF3AA3DA717F2CF05A93D33D` | `media/textures/Item_HandCrossBow.png` |
| `35441F0EE94AE29066D6BB90E5CB959BA14D782152DBF7D0219014B1F68C2D84` | `media/textures/Item_HandCrossBowDrawn.png` |
| `BD2F0F54FDB4D4FA95CAB74C83E162A914EB22D762646D144BD62C06CEAD0ADF` | `media/textures/Item_WoodBolt.png` |
| `14A80E65F923EF9B7D4D0A0070E5FE173A2F30D2B3BF072CAFEEC219F966C14D` | `media/textures/Item_BrokenWoodBolt.png` |
| `CB1D19F79AD147A4813F4C05BA3CD4183A6212B33C229940A9EA33804396BA70` | `media/textures/Item_WoodBoltShaft.png` |
| `7A67226E0A1D87F93F21AABACCEF0E103D64C380BE2B08DA025FC0B0E50D7660` | `media/textures/Item_ShortWoodBolt.png` |
| `63301A38F88706919FDB5A1A3872DCBFC4E287DE743DECA700728F9C65C632F4` | `media/textures/Item_ShortBrokenWoodBolt.png` |
| `ABD20F23685A41E8F066DD03828319B4CEAEA831371EC9FD7C856452796CA660` | `media/textures/Item_ShortWoodBoltShaft.png` |
| `9674FD5697EE658A4584D7C110E94DEF4DCD3BCE241899EC48E8864845969BDC` | `media/textures/Item_StoneBoltHead.png` |
| `9A3C5E7C369F76A8CE8942FC613BC7AD544FE3EC18CDFD77A9C5751157481331` | `media/textures/weapons/firearm/CrossBow.png` |
| `B332EAB3C4045901C4EC45101FF5451DF3017002A3FE136EB68AF5099E231F83` | `media/textures/weapons/firearm/CompoundCrossBow.png` |
| `78655396A5FA697DD7F5ADFF9DF911276ACEF332CEB6842D7A454D238558B7F3` | `media/textures/weapons/firearm/WoodBolt.png` |
| `05BD30103F57D570C7D1F3BA7973EC3350F793C5A08F6FBCB5C41047A0B2243D` | `media/models_x/weapons/firearm/CrossBow.fbx` |
| `3BA4E024AD671CF91DBC8FC8D0271914439505679DB121F667B5BDEE607E7281` | `media/models_x/weapons/firearm/CrossBowDrawn.fbx` |
| `77AB83199A5397552B35774F6CFAF15D5AAF4507E38A71F1FC23267A47600669` | `media/models_x/weapons/firearm/ImprovedCrossBow.fbx` |
| `C7941E9613C2AF992A345F2A7D44A58690389F893970C91EF93D272CEB615ED8` | `media/models_x/weapons/firearm/ImprovedCrossBowDrawn.fbx` |
| `F426A0036C82199675FE5EE9469F7B5F5136C1787622F7CCA99A5D7555A4C180` | `media/models_x/weapons/firearm/CompoundCrossBow.fbx` |
| `05DB178482933A7713394DDB5311A23FB52BB2952EE0DC3094A057CF15D70F28` | `media/models_x/weapons/firearm/CompoundCrossBowDrawn.fbx` |
| `780D9E2C893F33692094F99FBA81E35DC5FE0B1DD0D8A19D02D8BFFDEC568682` | `media/models_x/weapons/firearm/HandCrossBow.fbx` |
| `21DAD499ADD51CB45A6614D33D3D648DD7DEF82F3EBAC8E97A6ED6C4E39E4AE6` | `media/models_x/weapons/firearm/HandCrossBowDrawn.fbx` |
| `4BA4E69C21B322D05CE749BE5DB19721C0D6362251EC865073FA4D2C0C90C68F` | `media/models_x/weapons/firearm/WoodBolt.fbx` |
| `3867A625F27B766887F40CB569FF895D38C2DB223E85EDFD54A60E9DCA608AA2` | `media/models_x/weapons/firearm/ShortWoodBolt.fbx` |
| `F1EC9923A675B6179EE0B9E1B8C62012BDD05D181991B59E5308D96E717D2FFB` | `media/models_x/weapons/firearm/WoodBoltBroken.fbx` |
| `A82F38A2DC5B9DA3A494ADC7AE504658112E299154AB81F89DA47FB9E99141A6` | `media/sound/CrossbowShoot.ogg` |
| `106A08E5213DB173DB84ED1D29DE7B9E4CD38B52F57463FE12889B8E81FCDC44` | `media/sound/CompoundCrossBowShoot.ogg` |
| `219F41F195204C1F5F5DC4CA8FF037ED5ACC2C57EF8289ACA5651267DEFC4947` | `media/sound/CrossbowDryShot.ogg` |
| `9C4317B71E3E467280312F97F494367510C9D6C532ED9658E3D2DF8B381E3904` | `media/sound/CrossbowHitBlood.ogg` |
| `5B35D73FA49A35BECD69D854534771CADCD8E0597DC415971C57971B036A5DE1` | `media/sound/CrossbowReload.ogg` |
| `ADBBE6FE15DD7B746093DC4DD503FC19D8B114D35D415A0C0B88E3B9829CB77B` | `media/sound/CrossbowReloadStart.ogg` |
| `B0B856CA41C295B880C0C01C8D8FE655624AE1988AE192CE5CF10546C130DE35` | `media/sound/CrossbowReloadStop.ogg` |
| `047C85DA3AC6BE1A9C998DDA5E34D29B151082E9FF26FE6C41D8A2C67AAB35A7` | `media/sound/CompoundCrossBowReload.ogg` |
| `BA1F77EBDC3BC22B70833E19C6FC142D8AA23EFDB45DB574C6861B9A2A2B17AD` | `media/sound/CompoundCrossBowRack.ogg` |
| `C6B5D806CEACC51494D1347BCD33C597B0F4B9307C524A60FBAB904C22DB71E5` | `потрібні файли/2021CrossbowRust.ogg` |
