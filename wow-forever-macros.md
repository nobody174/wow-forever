# WoW Forever Macro Cheatsheet (nobody174 style)

Copy/paste macros for Priest, Shaman, Paladin, Warlock, Hunter and Warrior. Each class has a **Shared** section (every spec uses it) plus spec-only extras.

## Patterns

**Damage (Priest — target-of-target aware)**
```
#showtooltip SPELL
/cast [@targettarget, harm, exists][harm] SPELL
```

**Damage (every other class)**
```
#showtooltip SPELL
/cast [harm] SPELL
```

**Mouseover heal / utility**
```
#showtooltip SPELL
/cast [@mouseover, help, exists][help] SPELL
```

**Friend-or-foe (Dispel Magic)**
```
#showtooltip SPELL
/cast [@mouseover, exists][exists] SPELL
```

**Buffs (adds self fallback)**
```
#showtooltip SPELL
/cast [@mouseover, help, exists][help][@player] SPELL
```

**Spam-safe channel**
```
#showtooltip SPELL
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] SPELL
```

**Wand**
```
#showtooltip Shoot
/cast [@targettarget, harm, exists, nochanneling:Shoot] Shoot
/cast [harm, nochanneling:Shoot] Shoot
```

## Notes

- Spells without a rank cast your highest rank automatically.
- Buff macros add `[@player]` as a last fallback so they self-buff with no target. Delete it if you want the strict two-clause style.
- Item macros (`/use ...`) need the item name edited to the rank you carry.
- WoW Forever changes some classes/systems; if a spell name is renamed or missing in beta, swap the name and keep the pattern.
- Macro limit is 255 characters; every macro here fits.

## Universal (all classes)

### Targeting helpers

**Smart target enemy** — Only grabs a new enemy if you have no live hostile target.
```
/targetenemy [noharm][dead]
```

**Grab TT (take the mob off your friend)**
```
/target [@targettarget, harm, exists]
```

**Assist mouseover / friendly target**
```
/assist [@mouseover, help, exists][help]
```

**Clear dead target**
```
/cleartarget [dead]
```

**Skull mark mouseover / target** — 8 = skull, 7 = cross, 5 = moon, 6 = square. Uses the full /targetmarker name, not the /tm shorthand — the ThreatMaster addon claims /tm for itself, which silently breaks this macro if you use the short form.
```
/targetmarker [@mouseover, exists][] 8
```

### Focus

**Set focus (mouseover first)**
```
/focus [@mouseover, exists][]
```

**Clear focus**
```
/clearfocus
```

**Target focus**
```
/target focus
```

**Assist focus (set tank as focus)**
```
/assist focus
```

### Panic / defensive

**Healing potion** — Swap the item name to the potion rank you carry.
```
/use Major Healing Potion
```

**Mana potion** — Swap the item name to the potion rank you carry.
```
/use Major Mana Potion
```

### Misc / UI

**Zoom out more** — Raises the max camera zoom-out distance beyond the default cap.
```
/console cameraDistanceMaxZoomFactor 4
```

**Hide guild names** — Removes guild tags from nameplates and unit frames.
```
/console UnitNamePlayerGuild 0
```

**Hide PvP titles** — Removes PvP rank titles from nameplates and unit frames.
```
/console UnitNamePlayerPVPTitle 0
```

**Weapon swap: 1H+offhand ↔ 2H** — Swap the item names for your own gear. Toggles between 1H+offhand and 2H each press — slot 16 = main hand, 17 = off hand/shield.
```
/equipslot 16 Durgen's Crescent Axe
/equipslot 17 Veteran Shield
/equipslot 16 Ironforge Greathammer
```

## Priest

### Priest — Shared (all specs)

#### Damage / offensive

**Shadow Word: Pain**
```
#showtooltip Shadow Word: Pain
/cast [@targettarget, harm, exists][harm] Shadow Word: Pain
```

**Mind Blast**
```
#showtooltip Mind Blast
/cast [@targettarget, harm, exists][harm] Mind Blast
```

**Smite**
```
#showtooltip Smite
/cast [@targettarget, harm, exists][harm] Smite
```

**Holy Fire**
```
#showtooltip Holy Fire
/cast [@targettarget, harm, exists][harm] Holy Fire
```

**Mana Burn**
```
#showtooltip Mana Burn
/cast [@targettarget, harm, exists][harm] Mana Burn
```

#### Mouseover healing / utility

**Flash Heal**
```
#showtooltip Flash Heal
/cast [@mouseover, help, exists][help] Flash Heal
```

**Heal**
```
#showtooltip Heal
/cast [@mouseover, help, exists][help] Heal
```

**Greater Heal**
```
#showtooltip Greater Heal
/cast [@mouseover, help, exists][help] Greater Heal
```

**Lesser Heal**
```
#showtooltip Lesser Heal
/cast [@mouseover, help, exists][help] Lesser Heal
```

**Renew**
```
#showtooltip Renew
/cast [@mouseover, help, exists][help] Renew
```

**Power Word: Shield**
```
#showtooltip Power Word: Shield
/cast [@mouseover, help, exists][help] Power Word: Shield
```

**Prayer of Healing** — Party-wide, no target needed.
```
#showtooltip Prayer of Healing
/cast Prayer of Healing
```

**Resurrection**
```
#showtooltip Resurrection
/cast [@mouseover, help, exists][help] Resurrection
```

#### Cleanse / dispel

**Dispel Magic (friend or foe)**
```
#showtooltip Dispel Magic
/cast [@mouseover, exists][exists] Dispel Magic
```

**Cure Disease**
```
#showtooltip Cure Disease
/cast [@mouseover, help, exists][help] Cure Disease
```

**Abolish Disease**
```
#showtooltip Abolish Disease
/cast [@mouseover, help, exists][help] Abolish Disease
```

#### Wand / auto-attack

**Wand (spam-safe)**
```
#showtooltip Shoot
/cast [@targettarget, harm, exists, nochanneling:Shoot] Shoot
/cast [harm, nochanneling:Shoot] Shoot
```

#### Buffs

**Power Word: Fortitude**
```
#showtooltip Power Word: Fortitude
/cast [@mouseover, help, exists][help][@player] Power Word: Fortitude
```

**Prayer of Fortitude**
```
#showtooltip Prayer of Fortitude
/cast [@mouseover, help, exists][help][@player] Prayer of Fortitude
```

**Shadow Protection**
```
#showtooltip Shadow Protection
/cast [@mouseover, help, exists][help][@player] Shadow Protection
```

**Levitate**
```
#showtooltip Levitate
/cast [@mouseover, help, exists][help][@player] Levitate
```

**Inner Fire**
```
#showtooltip Inner Fire
/cast Inner Fire
```

**Fear Ward** — Racial/availability may differ in Forever.
```
#showtooltip Fear Ward
/cast [@mouseover, help, exists][help][@player] Fear Ward
```

#### Panic / defensive

**Shield self**
```
#showtooltip Power Word: Shield
/cast [@player] Power Word: Shield
```

**Psychic Scream**
```
#showtooltip Psychic Scream
/cast Psychic Scream
```

**Fade**
```
#showtooltip Fade
/cast Fade
```

**Desperate Prayer** — Racial priest spell.
```
#showtooltip Desperate Prayer
/cast Desperate Prayer
```

#### Focus

**Shackle Undead on focus**
```
#showtooltip Shackle Undead
/cast [@focus, harm, exists][harm] Shackle Undead
```

**Mind Control on focus**
```
#showtooltip Mind Control
/cast [@focus, harm, exists][harm] Mind Control
```

### Priest — Shadow

#### Damage / offensive

**Mind Flay (spam-safe)** — Won't clip an active channel.
```
#showtooltip Mind Flay
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Mind Flay
```

**Vampiric Embrace**
```
#showtooltip Vampiric Embrace
/cast [@targettarget, harm, exists][harm] Vampiric Embrace
```

**Silence (interrupt)** — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Silence
/stopcasting
/cast [@targettarget, harm, exists][harm] Silence
```

**Devouring Plague** — Racial priest spell.
```
#showtooltip Devouring Plague
/cast [@targettarget, harm, exists][harm] Devouring Plague
```

#### Buffs

**Shadowform (no cancel)** — Won't drop you out of form if pressed again.
```
#showtooltip Shadowform
/cast [noform] Shadowform
```

#### Focus

**Silence focus** — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Silence
/stopcasting
/cast [@focus, harm, exists][harm] Silence
```

### Priest — Holy

#### Mouseover healing / utility

**Inner Focus + Greater Heal**
```
#showtooltip Greater Heal
/cast Inner Focus
/cast [@mouseover, help, exists][help] Greater Heal
```

**Holy Nova**
```
#showtooltip Holy Nova
/cast Holy Nova
```

**Prayer of Mending** — New in Forever. Heals, then jumps to another group member when they take damage.
```
#showtooltip Prayer of Mending
/cast [@mouseover, help, exists][help] Prayer of Mending
```

**Lightwell**
```
#showtooltip Lightwell
/cast Lightwell
```

### Priest — Discipline

#### Mouseover healing / utility

**Power Infusion**
```
#showtooltip Power Infusion
/cast [@mouseover, help, exists][help] Power Infusion
```

**Penance (friend or foe)** — New in Forever. Heals a friendly mouseover/target, damages an enemy one.
```
#showtooltip Penance
/cast [@mouseover, exists][exists] Penance
```

**Inner Focus + Greater Heal**
```
#showtooltip Greater Heal
/cast Inner Focus
/cast [@mouseover, help, exists][help] Greater Heal
```

#### Buffs

**Divine Spirit**
```
#showtooltip Divine Spirit
/cast [@mouseover, help, exists][help][@player] Divine Spirit
```

## Warlock

### Warlock — Shared (all specs)

#### Damage / offensive

**Shadow Bolt + Imp Firebolt** — Sends your pet in and, when the Imp is out, fires its Firebolt on the same press. Handy if you keep Firebolt autocast off to stop the Imp pulling or burning mana. With any other demon the Firebolt line is skipped.
```
#showtooltip Shadow Bolt
/petattack [harm]
/cast [pet:Imp, harm] Firebolt
/cast [harm] Shadow Bolt
```

**Corruption**
```
#showtooltip Corruption
/cast [harm] Corruption
```

**Curse of Agony**
```
#showtooltip Curse of Agony
/cast [harm] Curse of Agony
```

**Immolate**
```
#showtooltip Immolate
/cast [harm] Immolate
```

**Searing Pain**
```
#showtooltip Searing Pain
/cast [harm] Searing Pain
```

**Soul Fire**
```
#showtooltip Soul Fire
/cast [harm] Soul Fire
```

**Death Coil**
```
#showtooltip Death Coil
/cast [harm] Death Coil
```

**Drain Life (spam-safe)**
```
#showtooltip Drain Life
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Drain Life
```

**Drain Soul (spam-safe)**
```
#showtooltip Drain Soul
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Drain Soul
```

**Drain Mana (spam-safe)**
```
#showtooltip Drain Mana
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Drain Mana
```

**Curse of the Elements**
```
#showtooltip Curse of the Elements
/cast [harm] Curse of the Elements
```

**Curse of Shadow**
```
#showtooltip Curse of Shadow
/cast [harm] Curse of Shadow
```

**Curse of Recklessness**
```
#showtooltip Curse of Recklessness
/cast [harm] Curse of Recklessness
```

**Curse of Weakness**
```
#showtooltip Curse of Weakness
/cast [harm] Curse of Weakness
```

**Curse of Tongues**
```
#showtooltip Curse of Tongues
/cast [harm] Curse of Tongues
```

**Hellfire**
```
#showtooltip Hellfire
/cast Hellfire
```

**Rain of Fire**
```
#showtooltip Rain of Fire
/cast Rain of Fire
```

#### Mouseover healing / utility

**Health Funnel (pet)**
```
#showtooltip Health Funnel
/cast Health Funnel
```

**Unending Breath**
```
#showtooltip Unending Breath
/cast [@mouseover, help, exists][help][@player] Unending Breath
```

**Detect Invisibility**
```
#showtooltip Detect Invisibility
/cast [@mouseover, help, exists][help][@player] Detect Invisibility
```

**Soulstone mouseover** — Swap item name to your soulstone rank.
```
/use [@mouseover, help, exists][help] Major Soulstone
```

#### Cleanse / dispel

**Devour Magic (Felhunter)**
```
#showtooltip Devour Magic
/cast [@mouseover, help, exists][help] Devour Magic
```

#### Wand / auto-attack

**Wand (spam-safe)**
```
#showtooltip Shoot
/cast [@targettarget, harm, exists, nochanneling:Shoot] Shoot
/cast [harm, nochanneling:Shoot] Shoot
```

#### Buffs

**Demon Armor**
```
#showtooltip Demon Armor
/cast Demon Armor
```

**Shadow Ward**
```
#showtooltip Shadow Ward
/cast Shadow Ward
```

#### Panic / defensive

**Healthstone** — Swap item name to your healthstone rank.
```
/use Major Healthstone
```

**Howl of Terror**
```
#showtooltip Howl of Terror
/cast Howl of Terror
```

**Fear**
```
#showtooltip Fear
/cast [harm] Fear
```

**Sacrifice (Voidwalker)**
```
#showtooltip Sacrifice
/cast Sacrifice
```

**Life Tap**
```
#showtooltip Life Tap
/cast Life Tap
```

#### Class QoL

**Pet attack TT / target**
```
/petattack [@targettarget, harm, exists][harm]
```

**Pet follow**
```
/petfollow
```

**Pet passive**
```
/petpassive
```

**Pet defensive**
```
/petdefensive
```

**Spell Lock (Felhunter)**
```
#showtooltip Spell Lock
/cast [harm] Spell Lock
```

**Torment (Voidwalker taunt)**
```
#showtooltip Torment
/cast [harm] Torment
```

**Summon Felhunter**
```
#showtooltip Summon Felhunter
/cast Summon Felhunter
```

**Summon Voidwalker**
```
#showtooltip Summon Voidwalker
/cast Summon Voidwalker
```

**Summon Succubus**
```
#showtooltip Summon Succubus
/cast Summon Succubus
```

**Summon Imp**
```
#showtooltip Summon Imp
/cast Summon Imp
```

#### Focus

**Fear focus**
```
#showtooltip Fear
/cast [@focus, harm, exists][harm] Fear
```

**Banish focus**
```
#showtooltip Banish
/cast [@focus, harm, exists][harm] Banish
```

**Seduction focus**
```
#showtooltip Seduction
/cast [@focus, harm, exists][harm] Seduction
```

**Spell Lock focus**
```
#showtooltip Spell Lock
/cast [@focus, harm, exists][harm] Spell Lock
```

**Enslave Demon focus**
```
#showtooltip Enslave Demon
/cast [@focus, harm, exists][harm] Enslave Demon
```

**Bane of Havoc focus** — New in Forever. Put it on a second mob (focus), then nuke your target: part of your damage is copied onto the focus.
```
#showtooltip Bane of Havoc
/cast [@focus, harm, exists][harm] Bane of Havoc
```

### Warlock — Affliction

#### Damage / offensive

**Siphon Life**
```
#showtooltip Siphon Life
/cast [harm] Siphon Life
```

**Curse of Exhaustion**
```
#showtooltip Curse of Exhaustion
/cast [harm] Curse of Exhaustion
```

**Wrack (spam-safe)** — New in Forever. Channeled drain that makes the target take more Shadow DoT damage.
```
#showtooltip Wrack
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Wrack
```

**Amplify Curse + Agony**
```
#showtooltip Curse of Agony
/cast Amplify Curse
/cast [harm] Curse of Agony
```

**DoT sequence (press to roll dots)**
```
#showtooltip Corruption
/castsequence [harm] reset=target Corruption, Curse of Agony, Siphon Life, Immolate
```

#### Panic / defensive

**Dark Pact** — Test in beta: not seen in the Forever beta talent tree, may be removed.
```
#showtooltip Dark Pact
/cast Dark Pact
```

### Warlock — Demonology

#### Class QoL

**Fel Domination + Felhunter**
```
#showtooltip Summon Felhunter
/cast Fel Domination
/cast Summon Felhunter
```

**Fel Domination + Voidwalker**
```
#showtooltip Summon Voidwalker
/cast Fel Domination
/cast Summon Voidwalker
```

**Soul Link**
```
#showtooltip Soul Link
/cast Soul Link
```

**Demonic Sacrifice**
```
#showtooltip Demonic Sacrifice
/cast Demonic Sacrifice
```

### Warlock — Destruction

#### Damage / offensive

**Conflagrate**
```
#showtooltip Conflagrate
/cast [harm] Conflagrate
```

**Shadowburn**
```
#showtooltip Shadowburn
/cast [harm] Shadowburn
```

**Incinerate** — New in Forever. Hits harder when Immolate is on the target.
```
#showtooltip Incinerate
/cast [harm] Incinerate
```

**Immolate > Conflagrate**
```
#showtooltip Immolate
/castsequence [harm] reset=target/10 Immolate, Conflagrate
```

## Mage

### Mage — Shared (all specs)

#### Damage / offensive

**Frostbolt**
```
#showtooltip Frostbolt
/cast [harm] Frostbolt
```

**Fireball**
```
#showtooltip Fireball
/cast [harm] Fireball
```

**Arcane Missiles (spam-safe)**
```
#showtooltip Arcane Missiles
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Arcane Missiles
```

**Arcane Explosion**
```
#showtooltip Arcane Explosion
/cast Arcane Explosion
```

**Fire Blast**
```
#showtooltip Fire Blast
/cast [harm] Fire Blast
```

**Frost Nova** — Clears your current cast first so the root fires instantly.
```
#showtooltip Frost Nova
/stopcasting
/cast [harm] Frost Nova
```

**Cone of Cold**
```
#showtooltip Cone of Cold
/cast Cone of Cold
```

**Scorch**
```
#showtooltip Scorch
/cast [harm] Scorch
```

**Counterspell (interrupt)** — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Counterspell
/stopcasting
/cast [harm] Counterspell
```

**Polymorph**
```
#showtooltip Polymorph
/cast [harm] Polymorph
```

**Polymorph + Diamond mark** — Marks the sheep target with a diamond so the group knows not to break it. Uses the full /targetmarker name, not /tm — the ThreatMaster addon claims /tm for itself, which silently breaks this macro if you use the short form.
```
#showtooltip Polymorph
/targetmarker [harm] 3
/cast [harm] Polymorph
```

#### Mouseover healing / utility

**Mana Shield**
```
#showtooltip Mana Shield
/cast Mana Shield
```

#### Cleanse / dispel

**Remove Curse (friend or foe)**
```
#showtooltip Remove Curse
/cast [@mouseover, exists][exists] Remove Curse
```

#### Buffs

**Arcane Intellect**
```
#showtooltip Arcane Intellect
/cast [@mouseover, help, exists][help][@player] Arcane Intellect
```

**Frost Armor**
```
#showtooltip Frost Armor
/cast Frost Armor
```

**Ice Armor**
```
#showtooltip Ice Armor
/cast Ice Armor
```

**Molten Armor**
```
#showtooltip Molten Armor
/cast Molten Armor
```

**Dampen Magic**
```
#showtooltip Dampen Magic
/cast [@mouseover, help, exists][help][@player] Dampen Magic
```

**Amplify Magic**
```
#showtooltip Amplify Magic
/cast [@mouseover, help, exists][help][@player] Amplify Magic
```

#### Panic / defensive

**Ice Block (press again to cancel)** — First press casts Ice Block, second press cancels it early.
```
#showtooltip Ice Block
/cancelaura Ice Block
/cast Ice Block
```

**Blink**
```
#showtooltip Blink
/cast Blink
```

**Evocation**
```
#showtooltip Evocation
/cast Evocation
```

#### Class QoL

**Conjure Food**
```
#showtooltip Conjure Food
/cast Conjure Food
```

**Conjure Water**
```
#showtooltip Conjure Water
/cast Conjure Water
```

**Summon Water Elemental**
```
#showtooltip Summon Water Elemental
/cast Summon Water Elemental
```

**Remove Curse**
```
#showtooltip Remove Curse
/cast [@mouseover, help, exists][help] Remove Curse
```

#### Focus

**Counterspell focus** — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Counterspell
/stopcasting
/cast [@focus, harm, exists][harm] Counterspell
```

**Polymorph focus**
```
#showtooltip Polymorph
/cast [@focus, harm, exists][harm] Polymorph
```

### Mage — Arcane

#### Damage / offensive

**Arcane Power + Arcane Missiles**
```
#showtooltip Arcane Missiles
/cast Arcane Power
/cast [harm] Arcane Missiles
```

**Presence of Mind + Frostbolt** — Instant-cast next spell.
```
#showtooltip Frostbolt
/cast Presence of Mind
/cast [harm] Frostbolt
```

**Presence of Mind + Pyroblast** — The classic burst combo for Arcane/Fire hybrids: instant Pyroblast.
```
#showtooltip Pyroblast
/cast Presence of Mind
/cast [harm] Pyroblast
```

**Arcane Blast** — New in Forever. Each cast in a row costs more and powers up your next other spell.
```
#showtooltip Arcane Blast
/cast [harm] Arcane Blast
```

### Mage — Fire

#### Damage / offensive

**Combustion**
```
#showtooltip Combustion
/cast Combustion
```

**Pyroblast**
```
#showtooltip Pyroblast
/cast [harm] Pyroblast
```

### Mage — Frost

#### Damage / offensive

**Ice Lance**
```
#showtooltip Ice Lance
/cast [harm] Ice Lance
```

**Cold Snap**
```
#showtooltip Cold Snap
/cast Cold Snap
```

## Rogue

### Rogue — Shared (all specs)

#### Damage / offensive

**Sinister Strike**
```
#showtooltip Sinister Strike
/cast [harm] Sinister Strike
```

**Backstab**
```
#showtooltip Backstab
/cast [harm] Backstab
```

**Eviscerate**
```
#showtooltip Eviscerate
/cast [harm] Eviscerate
```

**Gouge**
```
#showtooltip Gouge
/cast [harm] Gouge
```

**Kidney Shot**
```
#showtooltip Kidney Shot
/cast [harm] Kidney Shot
```

**Rupture**
```
#showtooltip Rupture
/cast [harm] Rupture
```

**Garrote** — Requires stealth.
```
#showtooltip Garrote
/cast [harm] Garrote
```

**Ambush** — Requires stealth.
```
#showtooltip Ambush
/cast [harm] Ambush
```

**Cheap Shot** — Requires stealth. Classic stunlock opener.
```
#showtooltip Cheap Shot
/cast [harm] Cheap Shot
```

**Expose Armor**
```
#showtooltip Expose Armor
/cast [harm] Expose Armor
```

**Sap** — Only works on an out-of-combat target.
```
#showtooltip Sap
/cast [harm] Sap
```

**Kick (interrupt)** — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Kick
/stopcasting
/cast [harm] Kick
```

#### Cleanse / dispel

*Rogues have no dispel. Interrupt instead with Kick, or silence with Gouge/Kidney Shot/Blind.*

#### Wand / auto-attack

**Auto-attack (spam-safe)**
```
/startattack [@targettarget, harm, exists][harm]
```

#### Buffs

**Slice and Dice**
```
#showtooltip Slice and Dice
/cast Slice and Dice
```

#### Panic / defensive

**Evasion**
```
#showtooltip Evasion
/cast Evasion
```

**Vanish**
```
#showtooltip Vanish
/cast Vanish
```

**Sprint**
```
#showtooltip Sprint
/cast Sprint
```

**Blind**
```
#showtooltip Blind
/cast [harm] Blind
```

#### Class QoL

**Stealth (no cancel)** — Won't drop you out of stealth if pressed again.
```
#showtooltip Stealth
/cast [nostealth] Stealth
```

**Pick Lock**
```
#showtooltip Pick Lock
/cast Pick Lock
```

**Pick Pocket**
```
#showtooltip Pick Pocket
/cast [harm] Pick Pocket
```

**Pick Pocket + Sap** — Pick Pocket has no global cooldown, so one press robs and saps.
```
#showtooltip Sap
/cast [harm] Pick Pocket
/cast [harm] Sap
```

**Apply poison to main hand** — Swap the item name to the poison you carry.
```
/use Instant Poison
/use Main Hand Weapon
```

**Apply poison to off hand** — Swap the item name to the poison you carry.
```
/use Deadly Poison
/use Off Hand Weapon
```

**Distract**
```
#showtooltip Distract
/cast [harm] Distract
```

**Feint**
```
#showtooltip Feint
/cast [harm] Feint
```

#### Focus

**Kick focus** — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Kick
/stopcasting
/cast [@focus, harm, exists][harm] Kick
```

**Kidney Shot focus**
```
#showtooltip Kidney Shot
/cast [@focus, harm, exists][harm] Kidney Shot
```

**Blind focus**
```
#showtooltip Blind
/cast [@focus, harm, exists][harm] Blind
```

### Rogue — Assassination

#### Damage / offensive

**Venom** — Forever's finisher (replaces Envenom): boosts poison damage and proc chance. Longer duration per combo point.
```
#showtooltip Venom
/cast [harm] Venom
```

**Mutilate**
```
#showtooltip Mutilate
/cast [harm] Mutilate
```

**Cold Blood + Ambush** — Requires stealth.
```
#showtooltip Ambush
/cast Cold Blood
/cast [harm] Ambush
```

### Rogue — Combat

#### Damage / offensive

**Blade Flurry**
```
#showtooltip Blade Flurry
/cast Blade Flurry
```

**Adrenaline Rush**
```
#showtooltip Adrenaline Rush
/cast Adrenaline Rush
```

### Rogue — Subtlety

#### Damage / offensive

**Hemorrhage**
```
#showtooltip Hemorrhage
/cast [harm] Hemorrhage
```

**Premeditation** — Requires stealth.
```
#showtooltip Premeditation
/cast Premeditation
```

#### Panic / defensive

**Cloak of Shadows**
```
#showtooltip Cloak of Shadows
/cast Cloak of Shadows
```

## Shaman

### Shaman — Shared (all specs)

#### Damage / offensive

**Lightning Bolt**
```
#showtooltip Lightning Bolt
/cast [harm] Lightning Bolt
```

**Chain Lightning**
```
#showtooltip Chain Lightning
/cast [harm] Chain Lightning
```

**Earth Shock (interrupt)** — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Earth Shock
/stopcasting
/cast [harm] Earth Shock
```

**Flame Shock**
```
#showtooltip Flame Shock
/cast [harm] Flame Shock
```

**Frost Shock**
```
#showtooltip Frost Shock
/cast [harm] Frost Shock
```

**Purge (offensive dispel)**
```
#showtooltip Purge
/cast [harm] Purge
```

#### Mouseover healing / utility

**Healing Wave**
```
#showtooltip Healing Wave
/cast [@mouseover, help, exists][help] Healing Wave
```

**Lesser Healing Wave**
```
#showtooltip Lesser Healing Wave
/cast [@mouseover, help, exists][help] Lesser Healing Wave
```

**Chain Heal**
```
#showtooltip Chain Heal
/cast [@mouseover, help, exists][help] Chain Heal
```

**Ancestral Spirit**
```
#showtooltip Ancestral Spirit
/cast [@mouseover, help, exists][help] Ancestral Spirit
```

**Riptide** — New in Forever. Instant heal + HoT that boosts your next Chain Heal.
```
#showtooltip Riptide
/cast [@mouseover, help, exists][help] Riptide
```

#### Cleanse / dispel

**Cure Poison**
```
#showtooltip Cure Poison
/cast [@mouseover, help, exists][help] Cure Poison
```

**Cure Disease**
```
#showtooltip Cure Disease
/cast [@mouseover, help, exists][help] Cure Disease
```

#### Wand / auto-attack

**Auto-attack (spam-safe)**
```
/startattack [@targettarget, harm, exists][harm]
```

#### Buffs

**Lightning Shield**
```
#showtooltip Lightning Shield
/cast Lightning Shield
```

**Water Shield** — New in Forever. Mana back when you're hit or crit-heal. Replaces Lightning Shield for healers.
```
#showtooltip Water Shield
/cast Water Shield
```

**Rockbiter Weapon**
```
#showtooltip Rockbiter Weapon
/cast Rockbiter Weapon
```

**Flametongue Weapon**
```
#showtooltip Flametongue Weapon
/cast Flametongue Weapon
```

**Frostbrand Weapon**
```
#showtooltip Frostbrand Weapon
/cast Frostbrand Weapon
```

**Water Walking**
```
#showtooltip Water Walking
/cast [@mouseover, help, exists][help][@player] Water Walking
```

**Water Breathing**
```
#showtooltip Water Breathing
/cast [@mouseover, help, exists][help][@player] Water Breathing
```

#### Panic / defensive

**Self Lesser Healing Wave**
```
#showtooltip Lesser Healing Wave
/cast [@player] Lesser Healing Wave
```

**Stoneclaw Totem**
```
#showtooltip Stoneclaw Totem
/cast Stoneclaw Totem
```

**Grounding Totem**
```
#showtooltip Grounding Totem
/cast Grounding Totem
```

**Ghost Wolf (no cancel)**
```
#showtooltip Ghost Wolf
/cast [noform] Ghost Wolf
```

#### Class QoL

**Totems: melee group (press 4x)**
```
#showtooltip Strength of Earth Totem
/castsequence reset=combat Strength of Earth Totem, Windfury Totem, Searing Totem, Mana Spring Totem
```

**Totems: caster group (press 4x)** — Swap Grace of Air for Tranquil Air if you prefer.
```
#showtooltip Stoneskin Totem
/castsequence reset=combat Stoneskin Totem, Grace of Air Totem, Searing Totem, Mana Spring Totem
```

**Tremor Totem**
```
#showtooltip Tremor Totem
/cast Tremor Totem
```

**Poison Cleansing Totem**
```
#showtooltip Poison Cleansing Totem
/cast Poison Cleansing Totem
```

**Disease Cleansing Totem**
```
#showtooltip Disease Cleansing Totem
/cast Disease Cleansing Totem
```

**Earthbind Totem**
```
#showtooltip Earthbind Totem
/cast Earthbind Totem
```

**Magma Totem**
```
#showtooltip Magma Totem
/cast Magma Totem
```

**Fire Nova Totem**
```
#showtooltip Fire Nova Totem
/cast Fire Nova Totem
```

**Healing Stream Totem**
```
#showtooltip Healing Stream Totem
/cast Healing Stream Totem
```

#### Focus

**Earth Shock interrupt on focus** — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Earth Shock
/stopcasting
/cast [@focus, harm, exists][harm] Earth Shock
```

**Purge focus**
```
#showtooltip Purge
/cast [@focus, harm, exists][harm] Purge
```

### Shaman — Elemental

#### Damage / offensive

**Lava Burst** — New in Forever. Hits 20% harder with your Flame Shock on the target.
```
#showtooltip Lava Burst
/cast [harm] Lava Burst
```

**Flame Shock > Lava Burst** — Opener: Flame Shock, then the boosted Lava Burst.
```
#showtooltip Flame Shock
/castsequence [harm] reset=target/12 Flame Shock, Lava Burst
```

**Elemental Mastery + Chain Lightning** — Test in beta: Elemental Mastery was not seen in the Forever beta talent tree.
```
#showtooltip Chain Lightning
/cast Elemental Mastery
/cast [harm] Chain Lightning
```

**Elemental Mastery + Lightning Bolt** — Test in beta: Elemental Mastery was not seen in the Forever beta talent tree.
```
#showtooltip Lightning Bolt
/cast Elemental Mastery
/cast [harm] Lightning Bolt
```

### Shaman — Enhancement

#### Damage / offensive

**Stormstrike** — Also starts auto-attack. In Forever it boosts only your NEXT Lightning Bolt, Chain Lightning or Earth Shock, so follow up with one.
```
#showtooltip Stormstrike
/cast [harm] Stormstrike
```

#### Buffs

**Windfury Weapon**
```
#showtooltip Windfury Weapon
/cast Windfury Weapon
```

**Windfury Weapon + Lightning Shield refresh** — Press twice to reapply both buffs; resets after 2 sec so it doesn't get stuck mid-sequence.
```
#showtooltip Lightning Shield
/castsequence reset=2 Lightning Shield, Windfury Weapon
```

## Hunter

### Hunter — Shared (all specs)

#### Damage / offensive

**Hunter's Mark**
```
#showtooltip Hunter's Mark
/cast [harm] Hunter's Mark
```

**Hunter's Mark + send pet (opener)** — One press marks the target and sends the pet in.
```
#showtooltip Hunter's Mark
/petattack [harm]
/cast [harm] Hunter's Mark
```

**Serpent Sting**
```
#showtooltip Serpent Sting
/cast [harm] Serpent Sting
```

**Arcane Shot**
```
#showtooltip Arcane Shot
/cast [harm] Arcane Shot
```

**Multi-Shot** — Forever: 0.5 sec cast, 6 sec cooldown. Stand still for it.
```
#showtooltip Multi-Shot
/cast [harm] Multi-Shot
```

**Volley at cursor** — Forever removed Volley's cooldown, so it's a real AoE button now. Drops at your mouse cursor, no targeting circle.
```
#showtooltip Volley
/cast [@cursor] Volley
```

**Concussive Shot**
```
#showtooltip Concussive Shot
/cast [harm] Concussive Shot
```

**Viper Sting**
```
#showtooltip Viper Sting
/cast [harm] Viper Sting
```

**Scorpid Sting**
```
#showtooltip Scorpid Sting
/cast [harm] Scorpid Sting
```

**Raptor Strike + Wing Clip**
```
#showtooltip Raptor Strike
/cast [harm] Raptor Strike
/cast [harm] Wing Clip
```

**Mongoose Bite**
```
#showtooltip Mongoose Bite
/cast [harm] Mongoose Bite
```

**Raptor Strike + Mongoose Bite + Wing Clip (test — GCD may skip some)** — Experimental 3-in-1. Only the first ability that both fires and consumes the GCD will actually go off per press — likely to just spam Raptor Strike. Testing to see how WoW Forever's client handles the fallthrough.
```
#showtooltip Raptor Strike
/cast [harm] Raptor Strike
/cast [harm] Mongoose Bite
/cast [harm] Wing Clip
```

**Wing Clip**
```
#showtooltip Wing Clip
/cast [harm] Wing Clip
```

**Distracting Shot**
```
#showtooltip Distracting Shot
/cast [harm] Distracting Shot
```

**Tranquilizing Shot (enrage dispel)** — Hunter's only dispel: removes Frenzy from enemies.
```
#showtooltip Tranquilizing Shot
/cast [harm] Tranquilizing Shot
```

#### Cleanse / dispel

*Hunters have no friendly cleanse. Use Tranquilizing Shot (Damage / offensive) instead.*

#### Wand / auto-attack

**Auto Shot (spam-safe)** — Hunter exception: ! stops Auto Shot toggling off. Unlike wand Shoot, it works here.
```
#showtooltip Auto Shot
/cast [@targettarget, harm, exists][harm] !Auto Shot
```

**Melee auto-attack**
```
/startattack [@targettarget, harm, exists][harm]
```

#### Buffs

**Aspect: Hawk in combat, Cheetah out**
```
#showtooltip Aspect of the Hawk
/cast [combat] Aspect of the Hawk; Aspect of the Cheetah
```

**Aspect toggle: Cheetah ↔ Hawk** — Each press swaps to the other aspect; the icon shows the next one. Resets after combat, so the first press after a fight is always Cheetah. Cheetah dazes you when hit, so press again before pulling.
```
#showtooltip
/castsequence reset=combat Aspect of the Cheetah, Aspect of the Hawk
```

**Aspect of the Hawk**
```
#showtooltip Aspect of the Hawk
/cast Aspect of the Hawk
```

**Aspect of the Monkey**
```
#showtooltip Aspect of the Monkey
/cast Aspect of the Monkey
```

**Aspect of the Pack**
```
#showtooltip Aspect of the Pack
/cast Aspect of the Pack
```

**Aspect of the Wild**
```
#showtooltip Aspect of the Wild
/cast Aspect of the Wild
```

#### Panic / defensive

**Feign Death (clean)** — Calls the pet back and stops attacking first, so the pet doesn't keep mobs on you.
```
#showtooltip Feign Death
/petfollow
/stopattack
/cast Feign Death
```

**Disengage**
```
#showtooltip Disengage
/cast [harm] Disengage
```

**Freezing Trap**
```
#showtooltip Freezing Trap
/cast Freezing Trap
```

**Frost Trap**
```
#showtooltip Frost Trap
/cast Frost Trap
```

**Rapid Fire**
```
#showtooltip Rapid Fire
/cast Rapid Fire
```

#### Class QoL

**Pet attack TT / target**
```
/petattack [@targettarget, harm, exists][harm]
```

**Pet attack mouseover** — Attacks the enemy under your mouse, else your target. No #showtooltip: /petattack is not a spell, so it would show a red ?. Pick the icon yourself in the macro window: the claw icon from the pet bar's Attack button (Ability_GhoulFrenzy).
```
/petattack [@mouseover, harm, exists][harm]
```

**Pet attack mouseover / TT** — Mouseover first, then your target's target, then your target. No #showtooltip: /petattack is not a spell, so it would show a red ?. Pick the icon yourself in the macro window: the claw icon from the pet bar's Attack button (Ability_GhoulFrenzy).
```
/petattack [@mouseover, harm, exists][@targettarget, harm, exists][harm]
```

**Pet attack / Shift = follow** — Press to send the pet (mouseover first); Shift+press calls it back. No #showtooltip: /petattack is not a spell, so it would show a red ?. Pick the icon yourself in the macro window: the claw icon from the pet bar's Attack button (Ability_GhoulFrenzy).
```
/petfollow [mod:shift]
/petattack [nomod:shift, @mouseover, harm, exists][nomod:shift, harm]
```

**Pet follow**
```
/petfollow
```

**Pet passive**
```
/petpassive
```

**Call / Revive / Mend (one button)**
```
#showtooltip Mend Pet
/cast [nopet] Call Pet; [@pet, dead] Revive Pet; Mend Pet
```

**Feed Pet** — Swap food item for your pet's diet.
```
#showtooltip Feed Pet
/cast Feed Pet
/use Tough Jerky
```

**Flare**
```
#showtooltip Flare
/cast Flare
```

**Explosive Trap**
```
#showtooltip Explosive Trap
/cast Explosive Trap
```

**Immolation Trap**
```
#showtooltip Immolation Trap
/cast Immolation Trap
```

#### Focus

**Hunter's Mark focus**
```
#showtooltip Hunter's Mark
/cast [@focus, harm, exists][harm] Hunter's Mark
```

**Concussive Shot focus**
```
#showtooltip Concussive Shot
/cast [@focus, harm, exists][harm] Concussive Shot
```

### Hunter — Beast Mastery

#### Damage / offensive

**Bestial Wrath + Rapid Fire burst**
```
#showtooltip Bestial Wrath
/cast Bestial Wrath
/cast Rapid Fire
```

**Intimidation + pet attack** — Intimidation only fires on the pet's next hit, so this sends the pet in too.
```
#showtooltip Intimidation
/petattack [harm]
/cast Intimidation
```

### Hunter — Marksmanship

#### Damage / offensive

**Aimed Shot**
```
#showtooltip Aimed Shot
/cast [harm] Aimed Shot
```

**Scatter Shot**
```
#showtooltip Scatter Shot
/cast [harm] Scatter Shot
```

#### Buffs

**Trueshot Aura**
```
#showtooltip Trueshot Aura
/cast Trueshot Aura
```

#### Focus

**Scatter Shot focus**
```
#showtooltip Scatter Shot
/cast [@focus, harm, exists][harm] Scatter Shot
```

### Hunter — Survival

#### Damage / offensive

**Counterattack**
```
#showtooltip Counterattack
/cast [harm] Counterattack
```

**Strider Kick** — New Survival talent in Forever: instant 100% weapon damage kick, 8 sec cooldown.
```
#showtooltip Strider Kick
/cast [harm] Strider Kick
```

**Survival melee button (Raptor + Mongoose + Strider Kick)** — Test in beta: Raptor Strike queues on your next swing (no global cooldown), then Mongoose Bite if it's lit up, else Strider Kick. Spam it in melee.
```
#showtooltip Raptor Strike
/startattack [harm]
/cast [harm] Raptor Strike
/cast [harm] Mongoose Bite
/cast [harm] Strider Kick
```

#### Panic / defensive

**Deterrence**
```
#showtooltip Deterrence
/cast Deterrence
```

## Paladin

### Paladin — Shared (all specs)

#### Damage / offensive

**Holy Strike + auto-attack** — New baseline strike in Forever (level 6, 12 sec cooldown).
```
#showtooltip Holy Strike
/startattack [harm]
/cast [harm] Holy Strike
```

**Judgement** — Forever: Judgement no longer uses up your seal, so no reseal needed.
```
#showtooltip Judgement
/cast [harm] Judgement
```

**Hammer of Wrath**
```
#showtooltip Hammer of Wrath
/cast [harm] Hammer of Wrath
```

**Exorcism**
```
#showtooltip Exorcism
/cast [harm] Exorcism
```

**Hammer of Justice**
```
#showtooltip Hammer of Justice
/cast [harm] Hammer of Justice
```

**Consecration**
```
#showtooltip Consecration
/cast Consecration
```

**Holy Wrath**
```
#showtooltip Holy Wrath
/cast Holy Wrath
```

#### Mouseover healing / utility

**Holy Light**
```
#showtooltip Holy Light
/cast [@mouseover, help, exists][help] Holy Light
```

**Flash of Light**
```
#showtooltip Flash of Light
/cast [@mouseover, help, exists][help] Flash of Light
```

**Lay on Hands**
```
#showtooltip Lay on Hands
/cast [@mouseover, help, exists][help] Lay on Hands
```

**Blessing of Protection**
```
#showtooltip Blessing of Protection
/cast [@mouseover, help, exists][help] Blessing of Protection
```

**Blessing of Freedom**
```
#showtooltip Blessing of Freedom
/cast [@mouseover, help, exists][help] Blessing of Freedom
```

**Redemption**
```
#showtooltip Redemption
/cast [@mouseover, help, exists][help] Redemption
```

#### Cleanse / dispel

**Cleanse**
```
#showtooltip Cleanse
/cast [@mouseover, help, exists][help] Cleanse
```

**Purify**
```
#showtooltip Purify
/cast [@mouseover, help, exists][help] Purify
```

#### Wand / auto-attack

**Auto-attack (spam-safe)**
```
/startattack [@targettarget, harm, exists][harm]
```

#### Buffs

**Blessing of Might**
```
#showtooltip Blessing of Might
/cast [@mouseover, help, exists][help][@player] Blessing of Might
```

**Blessing of Wisdom**
```
#showtooltip Blessing of Wisdom
/cast [@mouseover, help, exists][help][@player] Blessing of Wisdom
```

**Blessing of Salvation**
```
#showtooltip Blessing of Salvation
/cast [@mouseover, help, exists][help][@player] Blessing of Salvation
```

**Blessing of Light**
```
#showtooltip Blessing of Light
/cast [@mouseover, help, exists][help][@player] Blessing of Light
```

**Greater Blessing of Might**
```
#showtooltip Greater Blessing of Might
/cast [@mouseover, help, exists][help][@player] Greater Blessing of Might
```

**Greater Blessing of Wisdom**
```
#showtooltip Greater Blessing of Wisdom
/cast [@mouseover, help, exists][help][@player] Greater Blessing of Wisdom
```

**Devotion Aura**
```
#showtooltip Devotion Aura
/cast Devotion Aura
```

**Retribution Aura**
```
#showtooltip Retribution Aura
/cast Retribution Aura
```

**Concentration Aura**
```
#showtooltip Concentration Aura
/cast Concentration Aura
```

**Blessing of Kings** — Class spell at level 20 in Forever (was a Protection talent).
```
#showtooltip Blessing of Kings
/cast [@mouseover, help, exists][help][@player] Blessing of Kings
```

#### Panic / defensive

**Divine Shield (press again to cancel)** — First press bubbles, second press cancels it early.
```
#showtooltip Divine Shield
/cancelaura Divine Shield
/cast Divine Shield
```

**Divine Protection**
```
#showtooltip Divine Protection
/cast Divine Protection
```

**Lay on Hands self**
```
#showtooltip Lay on Hands
/cast [@player] Lay on Hands
```

**Blessing of Protection self (press again to cancel)** — BoP stops you from attacking, so the second press removes it.
```
#showtooltip Blessing of Protection
/cancelaura Blessing of Protection
/cast [@player] Blessing of Protection
```

**Voice of Truth** — New in Forever: 6 sec immunity to silence and interrupts. Use before a big heal/cast.
```
#showtooltip Voice of Truth
/cast Voice of Truth
```

#### Class QoL

**Seal of Righteousness**
```
#showtooltip Seal of Righteousness
/cast Seal of Righteousness
```

**Seal of the Crusader**
```
#showtooltip Seal of the Crusader
/cast Seal of the Crusader
```

**Seal of Wisdom**
```
#showtooltip Seal of Wisdom
/cast Seal of Wisdom
```

**Seal of Light**
```
#showtooltip Seal of Light
/cast Seal of Light
```

**Seal of Justice**
```
#showtooltip Seal of Justice
/cast Seal of Justice
```

**Divine Intervention**
```
#showtooltip Divine Intervention
/cast [@mouseover, help, exists][help] Divine Intervention
```

#### Focus

**Hammer of Justice focus**
```
#showtooltip Hammer of Justice
/cast [@focus, harm, exists][harm] Hammer of Justice
```

**Turn Undead focus**
```
#showtooltip Turn Undead
/cast [@focus, harm, exists][harm] Turn Undead
```

### Paladin — Retribution

#### Damage / offensive

**Repentance**
```
#showtooltip Repentance
/cast [harm] Repentance
```

#### Buffs

**Sanctity Aura**
```
#showtooltip Sanctity Aura
/cast Sanctity Aura
```

**Seal of Command**
```
#showtooltip Seal of Command
/cast Seal of Command
```

#### Class QoL

**Seal swap: Command <> Righteousness** — Test in beta: with the Twist of Light talent, switching seals lets your next swing also apply the old seal. Swap between swings.
```
#showtooltip
/castsequence Seal of Command, Seal of Righteousness
```

#### Focus

**Repentance focus**
```
#showtooltip Repentance
/cast [@focus, harm, exists][harm] Repentance
```

### Paladin — Holy

#### Mouseover healing / utility

**Holy Shock (friend or foe)** — Heals a friendly mouseover/target, damages an enemy one.
```
#showtooltip Holy Shock
/cast [@mouseover, exists][exists] Holy Shock
```

### Paladin — Protection

#### Damage / offensive

**Holy Shield** — Forever: a 4-charge block buff. Keep it up while tanking.
```
#showtooltip Holy Shield
/cast Holy Shield
```

**Judgement taunt (mouseover)** — With Seal of Fury active, Judgement taunts (10 yd). Hover a loose mob to pull it off the healer without changing target.
```
#showtooltip Judgement
/cast [@mouseover, harm, nodead][harm] Judgement
```

#### Buffs

**Seal of Fury** — New tank seal: Holy damage per hit + absorb shield with a shield equipped. Makes Judgement a taunt.
```
#showtooltip Seal of Fury
/cast Seal of Fury
```

**Righteous Fury**
```
#showtooltip Righteous Fury
/cast Righteous Fury
```

**Blessing of Sanctuary**
```
#showtooltip Blessing of Sanctuary
/cast [@mouseover, help, exists][help][@player] Blessing of Sanctuary
```

#### Panic / defensive

**Templar's Bulwark** — Talent. Absorb shield equal to your max health for 8 sec (5 min cooldown).
```
#showtooltip Templar's Bulwark
/cast Templar's Bulwark
```

#### Focus

**Judgement taunt on focus** — With Seal of Fury: taunt your focus (e.g. the add you're watching).
```
#showtooltip Judgement
/cast [@focus, harm, exists][harm] Judgement
```

## Warrior

### Warrior — Shared (all specs)

#### Damage / offensive

**Heroic Strike**
```
#showtooltip Heroic Strike
/cast [harm] Heroic Strike
```

**Cleave**
```
#showtooltip Cleave
/cast [harm] Cleave
```

**Rend**
```
#showtooltip Rend
/cast [harm] Rend
```

**Hamstring**
```
#showtooltip Hamstring
/cast [harm] Hamstring
```

**Sunder Armor**
```
#showtooltip Sunder Armor
/cast [harm] Sunder Armor
```

**Execute**
```
#showtooltip Execute
/cast [harm] Execute
```

**Overpower (to Battle)**
```
#showtooltip Overpower
/cast [nostance:1] Battle Stance; [@targettarget, harm, exists][harm] Overpower
```

**Demoralizing Shout**
```
#showtooltip Demoralizing Shout
/cast Demoralizing Shout
```

**Thunder Clap (to Battle)**
```
#showtooltip Thunder Clap
/cast [nostance:1] Battle Stance; Thunder Clap
```

#### Cleanse / dispel

*Warriors have no dispel. Interrupt instead with Pummel or Shield Bash.*

#### Wand / auto-attack

**Auto-attack (spam-safe)**
```
/startattack [@targettarget, harm, exists][harm]
```

#### Buffs

**Battle Shout**
```
#showtooltip Battle Shout
/cast Battle Shout
```

**Bloodrage**
```
#showtooltip Bloodrage
/cast Bloodrage
```

**Berserker Rage (to Berserker)**
```
#showtooltip Berserker Rage
/cast [nostance:3] Berserker Stance; Berserker Rage
```

#### Panic / defensive

**Shield Wall (to Defensive)**
```
#showtooltip Shield Wall
/cast [nostance:2] Defensive Stance; Shield Wall
```

**Retaliation (to Battle)**
```
#showtooltip Retaliation
/cast [nostance:1] Battle Stance; Retaliation
```

**Intimidating Shout**
```
#showtooltip Intimidating Shout
/cast [harm] Intimidating Shout
```

**Disarm (to Defensive)**
```
#showtooltip Disarm
/cast [nostance:2] Defensive Stance; [@targettarget, harm, exists][harm] Disarm
```

#### Class QoL

**Battle Stance**
```
#showtooltip Battle Stance
/cast Battle Stance
```

**Defensive Stance**
```
#showtooltip Defensive Stance
/cast Defensive Stance
```

**Berserker Stance**
```
#showtooltip Berserker Stance
/cast Berserker Stance
```

**Charge / Intercept (one button)** — Out of combat: Charge. In combat: Intercept. Stance swaps cost rage above your Tactical Mastery cap.
```
#showtooltip Charge
/cast [nocombat, nostance:1] Battle Stance; [nocombat, @targettarget, harm, exists][nocombat, harm] Charge; [nostance:3] Berserker Stance; [@targettarget, harm, exists][harm] Intercept
```

**Taunt (to Defensive)** — Target the friend being hit: TT is the mob.
```
#showtooltip Taunt
/cast [nostance:2] Defensive Stance; [@targettarget, harm, exists][harm] Taunt
```

**Mocking Blow (to Battle)**
```
#showtooltip Mocking Blow
/cast [nostance:1] Battle Stance; [@targettarget, harm, exists][harm] Mocking Blow
```

**Challenging Shout**
```
#showtooltip Challenging Shout
/cast Challenging Shout
```

**Charge + Rend (opener)** — Charges in (out of combat only) then immediately opens with Rend.
```
#showtooltip Charge
/cast [nocombat, nostance:1] Battle Stance
/cast [nocombat, harm] Charge
/cast [harm] Rend
```

**Stance dance (Battle -> Defensive -> Berserker)** — One button cycles Battle -> Defensive -> Berserker -> Battle.
```
#showtooltip Battle Stance
/cast [stance:1] Defensive Stance; [stance:2] Berserker Stance; [stance:3] Battle Stance
```

#### Focus

**Pummel focus**
```
#showtooltip Pummel
/cast [nostance:3] Berserker Stance; [@focus, harm, exists][harm] Pummel
```

**Shield Bash focus**
```
#showtooltip Shield Bash
/cast [@focus, harm, exists][harm] Shield Bash
```

**Taunt focus**
```
#showtooltip Taunt
/cast [@focus, harm, exists][harm] Taunt
```

### Warrior — Fury

#### Damage / offensive

**Bloodthirst**
```
#showtooltip Bloodthirst
/cast [harm] Bloodthirst
```

**Whirlwind (to Berserker)**
```
#showtooltip Whirlwind
/cast [nostance:3] Berserker Stance; Whirlwind
```

**Pummel (to Berserker)**
```
#showtooltip Pummel
/cast [nostance:3] Berserker Stance; [@targettarget, harm, exists][harm] Pummel
```

**Slam**
```
#showtooltip Slam
/cast [harm] Slam
```

**Piercing Howl**
```
#showtooltip Piercing Howl
/cast Piercing Howl
```

#### Buffs

**Death Wish**
```
#showtooltip Death Wish
/cast Death Wish
```

**Recklessness (to Berserker)**
```
#showtooltip Recklessness
/cast [nostance:3] Berserker Stance; Recklessness
```

### Warrior — Protection

#### Damage / offensive

**Shield Slam**
```
#showtooltip Shield Slam
/cast [harm] Shield Slam
```

**Sunder + Heroic Strike** — Heroic Strike has no global cooldown (it queues on your next swing), so it rides along with Sunder. Watch your rage.
```
#showtooltip Sunder Armor
/cast [harm] Heroic Strike
/cast [harm] Sunder Armor
```

**Revenge**
```
#showtooltip Revenge
/cast [harm] Revenge
```

**Shield Bash**
```
#showtooltip Shield Bash
/cast [harm] Shield Bash
```

**Concussion Blow**
```
#showtooltip Concussion Blow
/cast [harm] Concussion Blow
```

#### Panic / defensive

**Shield Block**
```
#showtooltip Shield Block
/cast Shield Block
```

**Last Stand**
```
#showtooltip Last Stand
/cast Last Stand
```
