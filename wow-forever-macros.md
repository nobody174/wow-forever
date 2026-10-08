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

**Mouseover heal / utility (adds self fallback)**
```
#showtooltip SPELL
/cast [@mouseover, help, exists][help][@player] SPELL
```

**Friend-or-foe, e.g. Dispel Magic (adds self fallback)**
```
#showtooltip SPELL
/cast [@mouseover, exists][exists][@player] SPELL
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
- Buff, heal/utility and friend-or-foe macros all add `[@player]` as a last fallback, so they hit you instead of doing nothing with no target. Delete it if you want the strict targeting-only style.
- Item macros (`/use ...`) need the item name edited to the rank you carry.
- WoW Forever changes some classes/systems; if a spell name is renamed or missing in beta, swap the name and keep the pattern.
- Macro limit is 255 characters; every macro here fits.

## Universal (all classes)

### Targeting helpers

**Smart target enemy** (`SmartTarget`) — Only grabs a new enemy if you have no live hostile target.
```
/targetenemy [noharm][dead]
```

**Grab TT (take the mob off your friend)** (`GrabTT`)
```
/target [@targettarget, harm, exists]
```

**Assist mouseover / friendly target** (`Assist@`)
```
/assist [@mouseover, help, exists][help]
```

**Clear dead target** (`ClearDead`)
```
/cleartarget [dead]
```

**Skull mark mouseover / target** (`SkullMark`) — 8 = skull, 7 = cross, 5 = moon, 6 = square. Uses the full /targetmarker name, not the /tm shorthand — the ThreatMaster addon claims /tm for itself, which silently breaks this macro if you use the short form.
```
/targetmarker [@mouseover, exists][] 8
```

### Focus

**Set focus (mouseover first)** (`SetFocus`)
```
/focus [@mouseover, exists][]
```

**Clear focus** (`ClearFocus`)
```
/clearfocus
```

**Target focus** (`TargetFoc`)
```
/target focus
```

**Assist focus (set tank as focus)** (`AssistFoc`)
```
/assist focus
```

### Panic / defensive

**Healing potion** (`HPotion`) — Swap the item name to the potion rank you carry.
```
/use Major Healing Potion
```

**Mana potion** (`MPotion`) — Swap the item name to the potion rank you carry.
```
/use Major Mana Potion
```

### Misc / UI

**Zoom out more** (`Zoom`) — Raises the max camera zoom-out distance beyond the default cap.
```
/console cameraDistanceMaxZoomFactor 4
```

**Hide guild names** (`HideGuild`) — Removes guild tags from nameplates and unit frames.
```
/console UnitNamePlayerGuild 0
```

**Hide PvP titles** (`HidePvP`) — Removes PvP rank titles from nameplates and unit frames.
```
/console UnitNamePlayerPVPTitle 0
```

**Weapon swap: 1H+offhand ↔ 2H** (`WeaponSwap`) — Swap the item names for your own gear. Toggles between 1H+offhand and 2H each press — slot 16 = main hand, 17 = off hand/shield.
```
/equipslot 16 Durgen's Crescent Axe
/equipslot 17 Veteran Shield
/equipslot 16 Ironforge Greathammer
```

## Priest

### Priest — Shared (all specs)

#### Damage / offensive

**Shadow Word: Pain** (`SWP`)
```
#showtooltip Shadow Word: Pain
/cast [@targettarget, harm, exists][harm] Shadow Word: Pain
```

**Mind Blast** (`MBlast`)
```
#showtooltip Mind Blast
/cast [@targettarget, harm, exists][harm] Mind Blast
```

**Smite** (`Smite`)
```
#showtooltip Smite
/cast [@targettarget, harm, exists][harm] Smite
```

**Holy Fire** (`HFire`)
```
#showtooltip Holy Fire
/cast [@targettarget, harm, exists][harm] Holy Fire
```

**Mana Burn** (`ManaBurn`)
```
#showtooltip Mana Burn
/cast [@targettarget, harm, exists][harm] Mana Burn
```

#### Mouseover healing / utility

**Flash Heal** (`FHeal`)
```
#showtooltip Flash Heal
/cast [@mouseover, help, exists][help][@player] Flash Heal
```

**Heal** (`Heal`)
```
#showtooltip Heal
/cast [@mouseover, help, exists][help][@player] Heal
```

**Greater Heal** (`GHeal`)
```
#showtooltip Greater Heal
/cast [@mouseover, help, exists][help][@player] Greater Heal
```

**Lesser Heal** (`LHeal`)
```
#showtooltip Lesser Heal
/cast [@mouseover, help, exists][help][@player] Lesser Heal
```

**Renew** (`Renew`)
```
#showtooltip Renew
/cast [@mouseover, help, exists][help][@player] Renew
```

**Power Word: Shield** (`PWS`)
```
#showtooltip Power Word: Shield
/cast [@mouseover, help, exists][help][@player] Power Word: Shield
```

**Prayer of Healing** (`PoH`) — Party-wide, no target needed.
```
#showtooltip Prayer of Healing
/cast Prayer of Healing
```

**Resurrection** (`Rez`)
```
#showtooltip Resurrection
/cast [@mouseover, help, exists][help][@player] Resurrection
```

#### Cleanse / dispel

**Dispel Magic (friend or foe)** (`Dispel`)
```
#showtooltip Dispel Magic
/cast [@mouseover, exists][exists][@player] Dispel Magic
```

**Cure Disease** (`CureDisease`)
```
#showtooltip Cure Disease
/cast [@mouseover, help, exists][help][@player] Cure Disease
```

**Abolish Disease** (`AbolishDis`)
```
#showtooltip Abolish Disease
/cast [@mouseover, help, exists][help][@player] Abolish Disease
```

#### Wand / auto-attack

**Wand (spam-safe)** (`Wand`)
```
#showtooltip Shoot
/cast [@targettarget, harm, exists, nochanneling:Shoot] Shoot
/cast [harm, nochanneling:Shoot] Shoot
```

#### Buffs

**Power Word: Fortitude** (`PWFort`)
```
#showtooltip Power Word: Fortitude
/cast [@mouseover, help, exists][help][@player] Power Word: Fortitude
```

**Prayer of Fortitude** (`PoFort`)
```
#showtooltip Prayer of Fortitude
/cast [@mouseover, help, exists][help][@player] Prayer of Fortitude
```

**Shadow Protection** (`ShadowProt`)
```
#showtooltip Shadow Protection
/cast [@mouseover, help, exists][help][@player] Shadow Protection
```

**Levitate** (`Levitate`)
```
#showtooltip Levitate
/cast [@mouseover, help, exists][help][@player] Levitate
```

**Inner Fire** (`InnerFire`)
```
#showtooltip Inner Fire
/cast Inner Fire
```

**Fear Ward** (`FearWard`) — Racial/availability may differ in Forever.
```
#showtooltip Fear Ward
/cast [@mouseover, help, exists][help][@player] Fear Ward
```

#### Panic / defensive

**Shield self** (`PWS me`)
```
#showtooltip Power Word: Shield
/cast [@player] Power Word: Shield
```

**Psychic Scream** (`Scream`)
```
#showtooltip Psychic Scream
/cast Psychic Scream
```

**Fade** (`Fade`)
```
#showtooltip Fade
/cast Fade
```

**Desperate Prayer** (`DesperatePr`) — Racial priest spell.
```
#showtooltip Desperate Prayer
/cast Desperate Prayer
```

#### Focus

**Shackle Undead on focus** (`Shackle F`)
```
#showtooltip Shackle Undead
/cast [@focus, harm, exists][harm] Shackle Undead
```

**Mind Control on focus** (`MindCtrl F`)
```
#showtooltip Mind Control
/cast [@focus, harm, exists][harm] Mind Control
```

### Priest — Shadow

#### Damage / offensive

**Mind Flay (spam-safe)** (`MFlay`) — Won't clip an active channel.
```
#showtooltip Mind Flay
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Mind Flay
```

**Vampiric Embrace** (`VampEmb`)
```
#showtooltip Vampiric Embrace
/cast [@targettarget, harm, exists][harm] Vampiric Embrace
```

**Silence (interrupt)** (`Silence`) — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Silence
/stopcasting
/cast [@targettarget, harm, exists][harm] Silence
```

**Devouring Plague** (`DevPlague`) — Racial priest spell.
```
#showtooltip Devouring Plague
/cast [@targettarget, harm, exists][harm] Devouring Plague
```

#### Buffs

**Shadowform (no cancel)** (`Shadowform`) — Won't drop you out of form if pressed again.
```
#showtooltip Shadowform
/cast [noform] Shadowform
```

#### Focus

**Silence focus** (`Silence F`) — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Silence
/stopcasting
/cast [@focus, harm, exists][harm] Silence
```

### Priest — Holy

#### Mouseover healing / utility

**Inner Focus + Greater Heal** (`IF+GHeal`)
```
#showtooltip Greater Heal
/cast Inner Focus
/cast [@mouseover, help, exists][help][@player] Greater Heal
```

**Holy Nova** (`HNova`)
```
#showtooltip Holy Nova
/cast Holy Nova
```

**Prayer of Mending** (`PoM`) — New in Forever. Heals, then jumps to another group member when they take damage.
```
#showtooltip Prayer of Mending
/cast [@mouseover, help, exists][help][@player] Prayer of Mending
```

**Lightwell** (`Lightwell`)
```
#showtooltip Lightwell
/cast Lightwell
```

### Priest — Discipline

#### Mouseover healing / utility

**Power Infusion** (`PowerInf`)
```
#showtooltip Power Infusion
/cast [@mouseover, help, exists][help][@player] Power Infusion
```

**Penance (friend or foe)** (`Penance`) — New in Forever. Heals a friendly mouseover/target, damages an enemy one.
```
#showtooltip Penance
/cast [@mouseover, exists][exists][@player] Penance
```

**Inner Focus + Greater Heal** (`InnerFocus`)
```
#showtooltip Greater Heal
/cast Inner Focus
/cast [@mouseover, help, exists][help][@player] Greater Heal
```

#### Buffs

**Divine Spirit** (`DivSpirit`)
```
#showtooltip Divine Spirit
/cast [@mouseover, help, exists][help][@player] Divine Spirit
```

## Warlock

### Warlock — Shared (all specs)

#### Damage / offensive

**Shadow Bolt + Imp Firebolt** (`ShadowBolt`) — Sends your pet in and, when the Imp is out, fires its Firebolt on the same press. Handy if you keep Firebolt autocast off to stop the Imp pulling or burning mana. With any other demon the Firebolt line is skipped.
```
#showtooltip Shadow Bolt
/petattack [harm]
/cast [pet:Imp, harm] Firebolt
/cast [harm] Shadow Bolt
```

**Corruption** (`Corrupt`)
```
#showtooltip Corruption
/cast [harm] Corruption
```

**Curse of Agony** (`CoAgony`)
```
#showtooltip Curse of Agony
/cast [harm] Curse of Agony
```

**Immolate** (`Immolate`)
```
#showtooltip Immolate
/cast [harm] Immolate
```

**Searing Pain** (`Searing`)
```
#showtooltip Searing Pain
/cast [harm] Searing Pain
```

**Soul Fire** (`SoulFire`)
```
#showtooltip Soul Fire
/cast [harm] Soul Fire
```

**Death Coil** (`DeathCoil`)
```
#showtooltip Death Coil
/cast [harm] Death Coil
```

**Drain Life (spam-safe)** (`DrainLife`)
```
#showtooltip Drain Life
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Drain Life
```

**Drain Soul (spam-safe)** (`DrainSoul`)
```
#showtooltip Drain Soul
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Drain Soul
```

**Drain Mana (spam-safe)** (`DrainMana`)
```
#showtooltip Drain Mana
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Drain Mana
```

**Curse of the Elements** (`CoElements`)
```
#showtooltip Curse of the Elements
/cast [harm] Curse of the Elements
```

**Curse of Shadow** (`CoShadow`)
```
#showtooltip Curse of Shadow
/cast [harm] Curse of Shadow
```

**Curse of Recklessness** (`CoReck`)
```
#showtooltip Curse of Recklessness
/cast [harm] Curse of Recklessness
```

**Curse of Weakness** (`CoWeak`)
```
#showtooltip Curse of Weakness
/cast [harm] Curse of Weakness
```

**Curse of Tongues** (`CoTongues`)
```
#showtooltip Curse of Tongues
/cast [harm] Curse of Tongues
```

**Hellfire** (`Hellfire`)
```
#showtooltip Hellfire
/cast Hellfire
```

**Rain of Fire** (`RoF`)
```
#showtooltip Rain of Fire
/cast Rain of Fire
```

#### Mouseover healing / utility

**Health Funnel (pet)** (`HFunnel`)
```
#showtooltip Health Funnel
/cast Health Funnel
```

**Unending Breath** (`UnendBreath`)
```
#showtooltip Unending Breath
/cast [@mouseover, help, exists][help][@player] Unending Breath
```

**Detect Invisibility** (`DetectInv`)
```
#showtooltip Detect Invisibility
/cast [@mouseover, help, exists][help][@player] Detect Invisibility
```

**Soulstone mouseover** (`Soulstone`) — Swap item name to your soulstone rank.
```
/use [@mouseover, help, exists][help] Major Soulstone
```

#### Cleanse / dispel

**Devour Magic (Felhunter)** (`DevourMagic`)
```
#showtooltip Devour Magic
/cast [@mouseover, help, exists][help][@player] Devour Magic
```

#### Wand / auto-attack

**Wand (spam-safe)** (`Wand`)
```
#showtooltip Shoot
/cast [@targettarget, harm, exists, nochanneling:Shoot] Shoot
/cast [harm, nochanneling:Shoot] Shoot
```

#### Buffs

**Demon Armor** (`DemonArmor`)
```
#showtooltip Demon Armor
/cast Demon Armor
```

**Shadow Ward** (`ShadowWard`)
```
#showtooltip Shadow Ward
/cast Shadow Ward
```

#### Panic / defensive

**Healthstone** (`Healthstone`) — Swap item name to your healthstone rank.
```
/use Major Healthstone
```

**Howl of Terror** (`HowlTerror`)
```
#showtooltip Howl of Terror
/cast Howl of Terror
```

**Fear** (`Fear`)
```
#showtooltip Fear
/cast [harm] Fear
```

**Sacrifice (Voidwalker)** (`Sacrifice`)
```
#showtooltip Sacrifice
/cast Sacrifice
```

**Life Tap** (`LifeTap`)
```
#showtooltip Life Tap
/cast Life Tap
```

#### Class QoL

**Pet attack TT / target** (`PetAtk`)
```
/petattack [@targettarget, harm, exists][harm]
```

**Pet follow** (`PetFollow`)
```
/petfollow
```

**Pet passive** (`PetPassive`)
```
/petpassive
```

**Pet defensive** (`PetDef`)
```
/petdefensive
```

**Spell Lock (Felhunter)** (`SpellLock`)
```
#showtooltip Spell Lock
/cast [harm] Spell Lock
```

**Torment (Voidwalker taunt)** (`Torment`)
```
#showtooltip Torment
/cast [harm] Torment
```

**Summon Felhunter** (`SummonFH`)
```
#showtooltip Summon Felhunter
/cast Summon Felhunter
```

**Summon Voidwalker** (`SummonVW`)
```
#showtooltip Summon Voidwalker
/cast Summon Voidwalker
```

**Summon Succubus** (`SummonSucc`)
```
#showtooltip Summon Succubus
/cast Summon Succubus
```

**Summon Imp** (`SummonImp`)
```
#showtooltip Summon Imp
/cast Summon Imp
```

#### Focus

**Fear focus** (`Fear F`)
```
#showtooltip Fear
/cast [@focus, harm, exists][harm] Fear
```

**Banish focus** (`Banish F`)
```
#showtooltip Banish
/cast [@focus, harm, exists][harm] Banish
```

**Seduction focus** (`Seduce F`)
```
#showtooltip Seduction
/cast [@focus, harm, exists][harm] Seduction
```

**Spell Lock focus** (`SpellLock F`)
```
#showtooltip Spell Lock
/cast [@focus, harm, exists][harm] Spell Lock
```

**Enslave Demon focus** (`Enslave F`)
```
#showtooltip Enslave Demon
/cast [@focus, harm, exists][harm] Enslave Demon
```

**Bane of Havoc focus** (`BoHavoc F`) — New in Forever. Put it on a second mob (focus), then nuke your target: part of your damage is copied onto the focus.
```
#showtooltip Bane of Havoc
/cast [@focus, harm, exists][harm] Bane of Havoc
```

### Warlock — Affliction

#### Damage / offensive

**Siphon Life** (`SiphonLife`)
```
#showtooltip Siphon Life
/cast [harm] Siphon Life
```

**Curse of Exhaustion** (`CoExhaust`)
```
#showtooltip Curse of Exhaustion
/cast [harm] Curse of Exhaustion
```

**Wrack (spam-safe)** (`Wrack`) — New in Forever. Channeled drain that makes the target take more Shadow DoT damage.
```
#showtooltip Wrack
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Wrack
```

**Amplify Curse + Agony** (`AmpCurse`)
```
#showtooltip Curse of Agony
/cast Amplify Curse
/cast [harm] Curse of Agony
```

**DoT sequence (press to roll dots)** (`DoTSeq`)
```
#showtooltip Corruption
/castsequence [harm] reset=target Corruption, Curse of Agony, Siphon Life, Immolate
```

#### Panic / defensive

**Dark Pact** (`DarkPact`) — Test in beta: not seen in the Forever beta talent tree, may be removed.
```
#showtooltip Dark Pact
/cast Dark Pact
```

### Warlock — Demonology

#### Class QoL

**Fel Domination + Felhunter** (`FelDom+FH`)
```
#showtooltip Summon Felhunter
/cast Fel Domination
/cast Summon Felhunter
```

**Fel Domination + Voidwalker** (`FelDom+VW`)
```
#showtooltip Summon Voidwalker
/cast Fel Domination
/cast Summon Voidwalker
```

**Soul Link** (`SoulLink`)
```
#showtooltip Soul Link
/cast Soul Link
```

**Demonic Sacrifice** (`DemonicSac`)
```
#showtooltip Demonic Sacrifice
/cast Demonic Sacrifice
```

### Warlock — Destruction

#### Damage / offensive

**Conflagrate** (`Conflag`)
```
#showtooltip Conflagrate
/cast [harm] Conflagrate
```

**Shadowburn** (`Shadowburn`)
```
#showtooltip Shadowburn
/cast [harm] Shadowburn
```

**Incinerate** (`Incinerate`) — New in Forever. Hits harder when Immolate is on the target.
```
#showtooltip Incinerate
/cast [harm] Incinerate
```

**Immolate > Conflagrate** (`Immo>Conflag`)
```
#showtooltip Immolate
/castsequence [harm] reset=target/10 Immolate, Conflagrate
```

## Mage

### Mage — Shared (all specs)

#### Damage / offensive

**Frostbolt** (`Frostbolt`)
```
#showtooltip Frostbolt
/cast [harm] Frostbolt
```

**Fireball** (`Fireball`)
```
#showtooltip Fireball
/cast [harm] Fireball
```

**Arcane Missiles (spam-safe)** (`ArcMissiles`)
```
#showtooltip Arcane Missiles
/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] Arcane Missiles
```

**Arcane Explosion** (`ArcExplosion`)
```
#showtooltip Arcane Explosion
/cast Arcane Explosion
```

**Fire Blast** (`FireBlast`)
```
#showtooltip Fire Blast
/cast [harm] Fire Blast
```

**Frost Nova** (`FrostNova`) — Clears your current cast first so the root fires instantly.
```
#showtooltip Frost Nova
/stopcasting
/cast [harm] Frost Nova
```

**Cone of Cold** (`ConeOfCold`)
```
#showtooltip Cone of Cold
/cast Cone of Cold
```

**Scorch** (`Scorch`)
```
#showtooltip Scorch
/cast [harm] Scorch
```

**Counterspell (interrupt)** (`CSpell`) — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Counterspell
/stopcasting
/cast [harm] Counterspell
```

**Polymorph** (`Polymorph`)
```
#showtooltip Polymorph
/cast [harm] Polymorph
```

**Polymorph + Diamond mark** (`Poly+Mark`) — Marks the sheep target with a diamond so the group knows not to break it. Uses the full /targetmarker name, not /tm — the ThreatMaster addon claims /tm for itself, which silently breaks this macro if you use the short form.
```
#showtooltip Polymorph
/targetmarker [harm] 3
/cast [harm] Polymorph
```

#### Mouseover healing / utility

**Mana Shield** (`ManaShield`)
```
#showtooltip Mana Shield
/cast Mana Shield
```

#### Cleanse / dispel

**Remove Curse (friend or foe)** (`RemCurse@`)
```
#showtooltip Remove Curse
/cast [@mouseover, exists][exists][@player] Remove Curse
```

#### Buffs

**Arcane Intellect** (`ArcInt`)
```
#showtooltip Arcane Intellect
/cast [@mouseover, help, exists][help][@player] Arcane Intellect
```

**Frost Armor** (`FrostArmor`)
```
#showtooltip Frost Armor
/cast Frost Armor
```

**Ice Armor** (`IceArmor`)
```
#showtooltip Ice Armor
/cast Ice Armor
```

**Molten Armor** (`MoltenArmor`)
```
#showtooltip Molten Armor
/cast Molten Armor
```

**Dampen Magic** (`DampenMagic`)
```
#showtooltip Dampen Magic
/cast [@mouseover, help, exists][help][@player] Dampen Magic
```

**Amplify Magic** (`AmpMagic`)
```
#showtooltip Amplify Magic
/cast [@mouseover, help, exists][help][@player] Amplify Magic
```

#### Panic / defensive

**Ice Block (press again to cancel)** (`IceBlock`) — First press casts Ice Block, second press cancels it early.
```
#showtooltip Ice Block
/cancelaura Ice Block
/cast Ice Block
```

**Blink** (`Blink`)
```
#showtooltip Blink
/cast Blink
```

**Evocation** (`Evocation`)
```
#showtooltip Evocation
/cast Evocation
```

#### Class QoL

**Conjure Food** (`ConjFood`)
```
#showtooltip Conjure Food
/cast Conjure Food
```

**Conjure Water** (`ConjWater`)
```
#showtooltip Conjure Water
/cast Conjure Water
```

**Summon Water Elemental** (`SummonWE`)
```
#showtooltip Summon Water Elemental
/cast Summon Water Elemental
```

**Remove Curse** (`RemoveCurse`)
```
#showtooltip Remove Curse
/cast [@mouseover, help, exists][help][@player] Remove Curse
```

#### Focus

**Counterspell focus** (`CSpell F`) — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Counterspell
/stopcasting
/cast [@focus, harm, exists][harm] Counterspell
```

**Polymorph focus** (`Poly F`)
```
#showtooltip Polymorph
/cast [@focus, harm, exists][harm] Polymorph
```

### Mage — Arcane

#### Damage / offensive

**Arcane Power + Arcane Missiles** (`APower+AMiss`)
```
#showtooltip Arcane Missiles
/cast Arcane Power
/cast [harm] Arcane Missiles
```

**Presence of Mind + Frostbolt** (`PoM+Frost`) — Instant-cast next spell.
```
#showtooltip Frostbolt
/cast Presence of Mind
/cast [harm] Frostbolt
```

**Presence of Mind + Pyroblast** (`PoM+Pyro`) — The classic burst combo for Arcane/Fire hybrids: instant Pyroblast.
```
#showtooltip Pyroblast
/cast Presence of Mind
/cast [harm] Pyroblast
```

**Arcane Blast** (`ArcBlast`) — New in Forever. Each cast in a row costs more and powers up your next other spell.
```
#showtooltip Arcane Blast
/cast [harm] Arcane Blast
```

### Mage — Fire

#### Damage / offensive

**Combustion** (`Combustion`)
```
#showtooltip Combustion
/cast Combustion
```

**Pyroblast** (`Pyroblast`)
```
#showtooltip Pyroblast
/cast [harm] Pyroblast
```

### Mage — Frost

#### Damage / offensive

**Ice Lance** (`IceLance`)
```
#showtooltip Ice Lance
/cast [harm] Ice Lance
```

**Cold Snap** (`ColdSnap`)
```
#showtooltip Cold Snap
/cast Cold Snap
```

## Rogue

### Rogue — Shared (all specs)

#### Damage / offensive

**Sinister Strike** (`SinStrike`)
```
#showtooltip Sinister Strike
/startattack [harm]
/cast [harm] Sinister Strike
```

**Backstab** (`Backstab`)
```
#showtooltip Backstab
/startattack [harm]
/cast [harm] Backstab
```

**Eviscerate** (`Evisc`)
```
#showtooltip Eviscerate
/startattack [harm]
/cast [harm] Eviscerate
```

**Gouge** (`Gouge`)
```
#showtooltip Gouge
/cast [harm] Gouge
```

**Gouge (mouseover)** (`Gouge@`)
```
#showtooltip Gouge
/cast [@mouseover, harm, nodead][harm, nodead] Gouge
```

**Kidney Shot** (`KidneyShot`)
```
#showtooltip Kidney Shot
/startattack [harm]
/cast [harm] Kidney Shot
```

**Rupture** (`Rupture`)
```
#showtooltip Rupture
/startattack [harm]
/cast [harm] Rupture
```

**Garrote** (`Garrote`) — Requires stealth.
```
#showtooltip Garrote
/startattack [harm]
/cast [harm] Garrote
```

**Ambush** (`Ambush`) — Requires stealth.
```
#showtooltip Ambush
/startattack [harm]
/cast [harm] Ambush
```

**Cheap Shot** (`CheapShot`) — Requires stealth. Classic stunlock opener.
```
#showtooltip Cheap Shot
/startattack [harm]
/cast [harm] Cheap Shot
```

**Expose Armor** (`ExposeArmor`)
```
#showtooltip Expose Armor
/cast [harm] Expose Armor
```

**Sap** (`Sap`) — Only works on an out-of-combat target.
```
#showtooltip Sap
/cast [harm] Sap
```

**Kick (interrupt)** (`Kick`) — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Kick
/stopcasting
/cast [harm] Kick
```

**Kick (mouseover)** (`Kick@`) — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Kick
/stopcasting
/cast [@mouseover, harm, nodead][harm, nodead] Kick
```

#### Cleanse / dispel

*Rogues have no dispel. Interrupt instead with Kick, or silence with Gouge/Kidney Shot/Blind.*

#### Wand / auto-attack

**Auto-attack (spam-safe)** (`Attack`)
```
/startattack [@targettarget, harm, exists][harm]
```

**Ranged weapon (Bow/Gun/Crossbow/Thrown)** (`Ranged`) — One button for whatever ranged weapon you have equipped.
```
#showtooltip
/cast [equipped:Bows] Shoot Bow; [equipped:Guns] Shoot Gun; [equipped:Crossbows] Shoot Crossbow; [equipped:Thrown] Throw
```

#### Buffs

**Slice and Dice** (`SnD`)
```
#showtooltip Slice and Dice
/cast Slice and Dice
```

#### Panic / defensive

**Evasion** (`Evasion`)
```
#showtooltip Evasion
/cast Evasion
```

**Vanish** (`Vanish`)
```
#showtooltip Vanish
/cast Vanish
```

**Sprint** (`Sprint`)
```
#showtooltip Sprint
/cast Sprint
```

**Blind** (`Blind`)
```
#showtooltip Blind
/cast [harm] Blind
```

**Blind (mouseover)** (`Blind@`)
```
#showtooltip Blind
/cast [@mouseover, harm, nodead][harm, nodead] Blind
```

#### Class QoL

**Stealth (no cancel)** (`Stealth`) — Won't drop you out of stealth if pressed again.
```
#showtooltip Stealth
/cast [nostealth] Stealth
```

**Pick Lock** (`PickLock`)
```
#showtooltip Pick Lock
/cast Pick Lock
```

**Pick Pocket** (`PickPocket`)
```
#showtooltip Pick Pocket
/cast [harm] Pick Pocket
```

**Pick Pocket (mouseover)** (`PickPkt@`)
```
#showtooltip Pick Pocket
/cast [@mouseover, harm, nodead][harm, nodead] Pick Pocket
```

**Pick Pocket + Sap** (`PickPkt+Sap`) — Pick Pocket has no global cooldown, so one press robs and saps.
```
#showtooltip Sap
/cast [harm] Pick Pocket
/cast [harm] Sap
```

**Apply poison (left = main, right = off hand)** (`Poison`) — Change the poison name to the rank you have (e.g. Instant Poison II). The last line confirms the "replace enchant" popup.
```
#showtooltip Instant Poison
/use Instant Poison
/use [button:1] 16; [button:2] 17
/click StaticPopup1Button1
```

**Distract** (`Distract`)
```
#showtooltip Distract
/cast [@cursor] Distract
```

**Feint** (`Feint`)
```
#showtooltip Feint
/cast [harm] Feint
```

**Grenade at cursor** (`Grenade`) — Swap the item name for the grenade you carry.
```
#showtooltip Iron Grenade
/use [@cursor] Iron Grenade
```

**Sharpening stone (left = main, right = off hand)** (`Stone`) — Swap the item name for the stone you carry. The last line confirms the "replace enchant" popup.
```
#showtooltip Rough Sharpening Stone
/use Rough Sharpening Stone
/use [button:1] 16; [button:2] 17
/click StaticPopup1Button1
```

#### Focus

**Kick focus** (`Kick F`) — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Kick
/stopcasting
/cast [@focus, harm, exists][harm] Kick
```

**Kidney Shot focus** (`KidneyShot F`)
```
#showtooltip Kidney Shot
/cast [@focus, harm, exists][harm] Kidney Shot
```

**Blind focus** (`Blind F`)
```
#showtooltip Blind
/cast [@focus, harm, exists][harm] Blind
```

### Rogue — Assassination

#### Damage / offensive

**Venom** (`Venom`) — Forever's finisher (replaces Envenom): boosts poison damage and proc chance. Longer duration per combo point.
```
#showtooltip Venom
/cast [harm] Venom
```

**Mutilate** (`Mutilate`)
```
#showtooltip Mutilate
/startattack [harm]
/cast [harm] Mutilate
```

**Cold Blood + Ambush** (`ColdBlood+Amb`) — Requires stealth.
```
#showtooltip Ambush
/cast Cold Blood
/cast [harm] Ambush
```

### Rogue — Combat

#### Damage / offensive

**Blade Flurry** (`BladeFlurry`)
```
#showtooltip Blade Flurry
/cast Blade Flurry
```

**Adrenaline Rush** (`AdrenRush`)
```
#showtooltip Adrenaline Rush
/cast Adrenaline Rush
```

### Rogue — Subtlety

#### Damage / offensive

**Hemorrhage** (`Hemo`)
```
#showtooltip Hemorrhage
/startattack [harm]
/cast [harm] Hemorrhage
```

**Premeditation** (`Premed`) — Requires stealth.
```
#showtooltip Premeditation
/cast Premeditation
```

#### Panic / defensive

**Cloak of Shadows** (`CloakShadow`)
```
#showtooltip Cloak of Shadows
/cast Cloak of Shadows
```

## Shaman

### Shaman — Shared (all specs)

#### Damage / offensive

**Lightning Bolt** (`LBolt`)
```
#showtooltip Lightning Bolt
/cast [harm] Lightning Bolt
```

**Chain Lightning** (`CLightning`)
```
#showtooltip Chain Lightning
/cast [harm] Chain Lightning
```

**Earth Shock (interrupt)** (`EShock`) — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Earth Shock
/stopcasting
/cast [harm] Earth Shock
```

**Flame Shock** (`FlameShock`)
```
#showtooltip Flame Shock
/cast [harm] Flame Shock
```

**Frost Shock** (`FrostShock`)
```
#showtooltip Frost Shock
/cast [harm] Frost Shock
```

**Purge (offensive dispel)** (`Purge`)
```
#showtooltip Purge
/cast [harm] Purge
```

#### Mouseover healing / utility

**Healing Wave** (`HWave`)
```
#showtooltip Healing Wave
/cast [@mouseover, help, exists][help][@player] Healing Wave
```

**Lesser Healing Wave** (`LHWave`)
```
#showtooltip Lesser Healing Wave
/cast [@mouseover, help, exists][help][@player] Lesser Healing Wave
```

**Chain Heal** (`ChainHeal`)
```
#showtooltip Chain Heal
/cast [@mouseover, help, exists][help][@player] Chain Heal
```

**Ancestral Spirit** (`AncSpirit`)
```
#showtooltip Ancestral Spirit
/cast [@mouseover, help, exists][help][@player] Ancestral Spirit
```

**Riptide** (`Riptide`) — New in Forever. Instant heal + HoT that boosts your next Chain Heal.
```
#showtooltip Riptide
/cast [@mouseover, help, exists][help][@player] Riptide
```

#### Cleanse / dispel

**Cure Poison** (`CurePoison`)
```
#showtooltip Cure Poison
/cast [@mouseover, help, exists][help][@player] Cure Poison
```

**Cure Disease** (`CureDisease`)
```
#showtooltip Cure Disease
/cast [@mouseover, help, exists][help][@player] Cure Disease
```

#### Wand / auto-attack

**Auto-attack (spam-safe)** (`Attack`)
```
/startattack [@targettarget, harm, exists][harm]
```

#### Buffs

**Lightning Shield** (`LShield`)
```
#showtooltip Lightning Shield
/cast Lightning Shield
```

**Water Shield** (`WShield`) — New in Forever. Mana back when you're hit or crit-heal. Replaces Lightning Shield for healers.
```
#showtooltip Water Shield
/cast Water Shield
```

**Rockbiter Weapon** (`Rockbiter`)
```
#showtooltip Rockbiter Weapon
/cast Rockbiter Weapon
```

**Flametongue Weapon** (`Flametongue`)
```
#showtooltip Flametongue Weapon
/cast Flametongue Weapon
```

**Frostbrand Weapon** (`Frostbrand`)
```
#showtooltip Frostbrand Weapon
/cast Frostbrand Weapon
```

**Water Walking** (`WaterWalk`)
```
#showtooltip Water Walking
/cast [@mouseover, help, exists][help][@player] Water Walking
```

**Water Breathing** (`WaterBreath`)
```
#showtooltip Water Breathing
/cast [@mouseover, help, exists][help][@player] Water Breathing
```

#### Panic / defensive

**Self Lesser Healing Wave** (`SelfLHWave`)
```
#showtooltip Lesser Healing Wave
/cast [@player] Lesser Healing Wave
```

**Stoneclaw Totem** (`Stoneclaw`)
```
#showtooltip Stoneclaw Totem
/cast Stoneclaw Totem
```

**Grounding Totem** (`Grounding`)
```
#showtooltip Grounding Totem
/cast Grounding Totem
```

**Ghost Wolf (no cancel)** (`GhostWolf`)
```
#showtooltip Ghost Wolf
/cast [noform] Ghost Wolf
```

#### Class QoL

**Totems: melee group (press 4x)** (`MeleeTotems`)
```
#showtooltip Strength of Earth Totem
/castsequence reset=combat Strength of Earth Totem, Windfury Totem, Searing Totem, Mana Spring Totem
```

**Totems: caster group (press 4x)** (`CasterTotems`) — Swap Grace of Air for Tranquil Air if you prefer.
```
#showtooltip Stoneskin Totem
/castsequence reset=combat Stoneskin Totem, Grace of Air Totem, Searing Totem, Mana Spring Totem
```

**Tremor Totem** (`Tremor`)
```
#showtooltip Tremor Totem
/cast Tremor Totem
```

**Poison Cleansing Totem** (`PoisonCleanse`)
```
#showtooltip Poison Cleansing Totem
/cast Poison Cleansing Totem
```

**Disease Cleansing Totem** (`DiseaseCleanse`)
```
#showtooltip Disease Cleansing Totem
/cast Disease Cleansing Totem
```

**Earthbind Totem** (`Earthbind`)
```
#showtooltip Earthbind Totem
/cast Earthbind Totem
```

**Magma Totem** (`Magma`)
```
#showtooltip Magma Totem
/cast Magma Totem
```

**Fire Nova Totem** (`FireNova`)
```
#showtooltip Fire Nova Totem
/cast Fire Nova Totem
```

**Healing Stream Totem** (`HealStream`)
```
#showtooltip Healing Stream Totem
/cast Healing Stream Totem
```

#### Focus

**Earth Shock interrupt on focus** (`EShock F`) — Clears your current cast first so the interrupt fires instantly.
```
#showtooltip Earth Shock
/stopcasting
/cast [@focus, harm, exists][harm] Earth Shock
```

**Purge focus** (`Purge F`)
```
#showtooltip Purge
/cast [@focus, harm, exists][harm] Purge
```

### Shaman — Elemental

#### Damage / offensive

**Lava Burst** (`LavaBurst`) — New in Forever. Hits 20% harder with your Flame Shock on the target.
```
#showtooltip Lava Burst
/cast [harm] Lava Burst
```

**Flame Shock > Lava Burst** (`Flame>Lava`) — Opener: Flame Shock, then the boosted Lava Burst.
```
#showtooltip Flame Shock
/castsequence [harm] reset=target/12 Flame Shock, Lava Burst
```

**Elemental Mastery + Chain Lightning** (`EleMastery+CL`) — Test in beta: Elemental Mastery was not seen in the Forever beta talent tree.
```
#showtooltip Chain Lightning
/cast Elemental Mastery
/cast [harm] Chain Lightning
```

**Elemental Mastery + Lightning Bolt** (`EleMastery+LB`) — Test in beta: Elemental Mastery was not seen in the Forever beta talent tree.
```
#showtooltip Lightning Bolt
/cast Elemental Mastery
/cast [harm] Lightning Bolt
```

### Shaman — Enhancement

#### Damage / offensive

**Stormstrike** (`Stormstrike`) — Also starts auto-attack. In Forever it boosts only your NEXT Lightning Bolt, Chain Lightning or Earth Shock, so follow up with one.
```
#showtooltip Stormstrike
/cast [harm] Stormstrike
```

#### Buffs

**Windfury Weapon** (`Windfury`)
```
#showtooltip Windfury Weapon
/cast Windfury Weapon
```

**Windfury Weapon + Lightning Shield refresh** (`WF+LSRefresh`) — Press twice to reapply both buffs; resets after 2 sec so it doesn't get stuck mid-sequence.
```
#showtooltip Lightning Shield
/castsequence reset=2 Lightning Shield, Windfury Weapon
```

## Hunter

### Hunter — Shared (all specs)

#### Damage / offensive

**Hunter's Mark** (`HMark`)
```
#showtooltip Hunter's Mark
/cast [harm] Hunter's Mark
```

**Hunter's Mark + send pet (opener)** (`HMark+Pet`) — One press marks the target and sends the pet in.
```
#showtooltip Hunter's Mark
/petattack [harm]
/cast [harm] Hunter's Mark
```

**Serpent Sting** (`SerpentSting`)
```
#showtooltip Serpent Sting
/cast [harm] Serpent Sting
```

**Arcane Shot** (`ArcaneShot`)
```
#showtooltip Arcane Shot
/cast [harm] Arcane Shot
```

**Multi-Shot** (`MultiShot`) — Forever: 0.5 sec cast, 6 sec cooldown. Stand still for it.
```
#showtooltip Multi-Shot
/cast [harm] Multi-Shot
```

**Volley at cursor** (`Volley`) — Forever removed Volley's cooldown, so it's a real AoE button now. Drops at your mouse cursor, no targeting circle.
```
#showtooltip Volley
/cast [@cursor] Volley
```

**Concussive Shot** (`ConcShot`)
```
#showtooltip Concussive Shot
/cast [harm] Concussive Shot
```

**Viper Sting** (`ViperSting`)
```
#showtooltip Viper Sting
/cast [harm] Viper Sting
```

**Scorpid Sting** (`ScorpidSting`)
```
#showtooltip Scorpid Sting
/cast [harm] Scorpid Sting
```

**Raptor Strike + Wing Clip** (`Raptor+Clip`)
```
#showtooltip Raptor Strike
/cast [harm] Raptor Strike
/cast [harm] Wing Clip
```

**Mongoose Bite** (`Mongoose`)
```
#showtooltip Mongoose Bite
/cast [harm] Mongoose Bite
```

**Raptor Strike + Mongoose Bite + Wing Clip (test — GCD may skip some)** (`Raptor3in1`) — Experimental 3-in-1. Only the first ability that both fires and consumes the GCD will actually go off per press — likely to just spam Raptor Strike. Testing to see how WoW Forever's client handles the fallthrough.
```
#showtooltip Raptor Strike
/cast [harm] Raptor Strike
/cast [harm] Mongoose Bite
/cast [harm] Wing Clip
```

**Wing Clip** (`WingClip`)
```
#showtooltip Wing Clip
/cast [harm] Wing Clip
```

**Distracting Shot** (`DistractShot`)
```
#showtooltip Distracting Shot
/cast [harm] Distracting Shot
```

**Tranquilizing Shot (enrage dispel)** (`TranqShot`) — Hunter's only dispel: removes Frenzy from enemies.
```
#showtooltip Tranquilizing Shot
/cast [harm] Tranquilizing Shot
```

#### Cleanse / dispel

*Hunters have no friendly cleanse. Use Tranquilizing Shot (Damage / offensive) instead.*

#### Wand / auto-attack

**Auto Shot (spam-safe)** (`AutoShot`) — Hunter exception: ! stops Auto Shot toggling off. Unlike wand Shoot, it works here.
```
#showtooltip Auto Shot
/cast [@targettarget, harm, exists][harm] !Auto Shot
```

**Melee auto-attack** (`Attack`)
```
/startattack [@targettarget, harm, exists][harm]
```

#### Buffs

**Aspect: Hawk in combat, Cheetah out** (`AspectHawk`)
```
#showtooltip Aspect of the Hawk
/cast [combat] Aspect of the Hawk; Aspect of the Cheetah
```

**Aspect toggle: Cheetah ↔ Hawk** (`AspectToggle`) — Each press swaps to the other aspect; the icon shows the next one. Resets after combat, so the first press after a fight is always Cheetah. Cheetah dazes you when hit, so press again before pulling.
```
#showtooltip
/castsequence reset=combat Aspect of the Cheetah, Aspect of the Hawk
```

**Aspect of the Hawk** (`AspHawk`)
```
#showtooltip Aspect of the Hawk
/cast Aspect of the Hawk
```

**Aspect of the Monkey** (`AspMonkey`)
```
#showtooltip Aspect of the Monkey
/cast Aspect of the Monkey
```

**Aspect of the Pack** (`AspPack`)
```
#showtooltip Aspect of the Pack
/cast Aspect of the Pack
```

**Aspect of the Wild** (`AspWild`)
```
#showtooltip Aspect of the Wild
/cast Aspect of the Wild
```

#### Panic / defensive

**Feign Death (clean)** (`FeignDeath`) — Calls the pet back and stops attacking first, so the pet doesn't keep mobs on you.
```
#showtooltip Feign Death
/petfollow
/stopattack
/cast Feign Death
```

**Disengage** (`Disengage`)
```
#showtooltip Disengage
/cast [harm] Disengage
```

**Freezing Trap** (`FreezeTrap`)
```
#showtooltip Freezing Trap
/cast Freezing Trap
```

**Frost Trap** (`FrostTrap`)
```
#showtooltip Frost Trap
/cast Frost Trap
```

**Rapid Fire** (`RapidFire`)
```
#showtooltip Rapid Fire
/cast Rapid Fire
```

#### Class QoL

**Pet attack TT / target** (`PetAtk`)
```
/petattack [@targettarget, harm, exists][harm]
```

**Pet attack mouseover** (`PetAtkMO`) — Attacks the enemy under your mouse, else your target. No #showtooltip: /petattack is not a spell, so it would show a red ?. Pick the icon yourself in the macro window: the claw icon from the pet bar's Attack button (Ability_GhoulFrenzy).
```
/petattack [@mouseover, harm, exists][harm]
```

**Pet attack mouseover / TT** (`PetAtkMOTT`) — Mouseover first, then your target's target, then your target. No #showtooltip: /petattack is not a spell, so it would show a red ?. Pick the icon yourself in the macro window: the claw icon from the pet bar's Attack button (Ability_GhoulFrenzy).
```
/petattack [@mouseover, harm, exists][@targettarget, harm, exists][harm]
```

**Pet attack / Shift = follow** (`PetAtkShift`) — Press to send the pet (mouseover first); Shift+press calls it back. No #showtooltip: /petattack is not a spell, so it would show a red ?. Pick the icon yourself in the macro window: the claw icon from the pet bar's Attack button (Ability_GhoulFrenzy).
```
/petfollow [mod:shift]
/petattack [nomod:shift, @mouseover, harm, exists][nomod:shift, harm]
```

**Pet follow** (`PetFollow`)
```
/petfollow
```

**Pet passive** (`PetPassive`)
```
/petpassive
```

**Call / Revive / Mend (one button)** (`PetMend`)
```
#showtooltip Mend Pet
/cast [nopet] Call Pet; [@pet, dead] Revive Pet; Mend Pet
```

**Feed Pet** (`FeedPet`) — Swap food item for your pet's diet.
```
#showtooltip Feed Pet
/cast Feed Pet
/use Tough Jerky
```

**Flare** (`Flare`)
```
#showtooltip Flare
/cast Flare
```

**Explosive Trap** (`ExploTrap`)
```
#showtooltip Explosive Trap
/cast Explosive Trap
```

**Immolation Trap** (`ImmoTrap`)
```
#showtooltip Immolation Trap
/cast Immolation Trap
```

#### Focus

**Hunter's Mark focus** (`HMark F`)
```
#showtooltip Hunter's Mark
/cast [@focus, harm, exists][harm] Hunter's Mark
```

**Concussive Shot focus** (`ConcShot F`)
```
#showtooltip Concussive Shot
/cast [@focus, harm, exists][harm] Concussive Shot
```

### Hunter — Beast Mastery

#### Damage / offensive

**Bestial Wrath + Rapid Fire burst** (`BW+RapidFire`)
```
#showtooltip Bestial Wrath
/cast Bestial Wrath
/cast Rapid Fire
```

**Intimidation + pet attack** (`Intim+Pet`) — Intimidation only fires on the pet's next hit, so this sends the pet in too.
```
#showtooltip Intimidation
/petattack [harm]
/cast Intimidation
```

### Hunter — Marksmanship

#### Damage / offensive

**Aimed Shot** (`AimedShot`)
```
#showtooltip Aimed Shot
/cast [harm] Aimed Shot
```

**Scatter Shot** (`ScatterShot`)
```
#showtooltip Scatter Shot
/cast [harm] Scatter Shot
```

#### Buffs

**Trueshot Aura** (`TrueshotAura`)
```
#showtooltip Trueshot Aura
/cast Trueshot Aura
```

#### Focus

**Scatter Shot focus** (`ScatterShot F`)
```
#showtooltip Scatter Shot
/cast [@focus, harm, exists][harm] Scatter Shot
```

### Hunter — Survival

#### Damage / offensive

**Counterattack** (`Counterattack`)
```
#showtooltip Counterattack
/cast [harm] Counterattack
```

**Strider Kick** (`StriderKick`) — New Survival talent in Forever: instant 100% weapon damage kick, 8 sec cooldown.
```
#showtooltip Strider Kick
/cast [harm] Strider Kick
```

**Survival melee button (Raptor + Mongoose + Strider Kick)** (`SurvMelee`) — Test in beta: Raptor Strike queues on your next swing (no global cooldown), then Mongoose Bite if it's lit up, else Strider Kick. Spam it in melee.
```
#showtooltip Raptor Strike
/startattack [harm]
/cast [harm] Raptor Strike
/cast [harm] Mongoose Bite
/cast [harm] Strider Kick
```

#### Panic / defensive

**Deterrence** (`Deterrence`)
```
#showtooltip Deterrence
/cast Deterrence
```

## Paladin

### Paladin — General (all specs)

#### Damage / offensive

**Holy Strike + auto-attack** (`HStrike`) — New baseline strike in Forever (level 6, 12 sec cooldown).
```
#showtooltip Holy Strike
/startattack [harm]
/cast [harm] Holy Strike
```

**Judgement** (`Judge`) — Forever: Judgement no longer uses up your seal, so no reseal needed.
```
#showtooltip Judgement
/cast [harm] Judgement
```

**Hammer of Wrath** (`HoW`)
```
#showtooltip Hammer of Wrath
/cast [harm] Hammer of Wrath
```

**Exorcism** (`Exo`)
```
#showtooltip Exorcism
/cast [harm] Exorcism
```

**Hammer of Justice** (`HoJ`) — Stuns whatever's under your mouse without changing your target; falls back to your target if nothing's under the mouse.
```
#showtooltip Hammer of Justice
/cast [@mouseover, harm, exists][harm] Hammer of Justice
```

**Consecration** (`Consec`)
```
#showtooltip Consecration
/cast Consecration
```

**Holy Wrath** (`HWrath`)
```
#showtooltip Holy Wrath
/cast Holy Wrath
```

#### Mouseover healing / utility

**Holy Light** (`HL`)
```
#showtooltip Holy Light
/cast [@mouseover, help, exists][help][@player] Holy Light
```

**Flash of Light** (`FoL`)
```
#showtooltip Flash of Light
/cast [@mouseover, help, exists][help][@player] Flash of Light
```

**Lay on Hands** (`LoH`)
```
#showtooltip Lay on Hands
/cast [@mouseover, help, exists][help][@player] Lay on Hands
```

**Blessing of Protection** (`BoP`)
```
#showtooltip Blessing of Protection
/cast [@mouseover, help, exists][help][@player] Blessing of Protection
```

**Blessing of Freedom** (`BoF`)
```
#showtooltip Blessing of Freedom
/cast [@mouseover, help, exists][help][@player] Blessing of Freedom
```

**Redemption** (`Rez`)
```
#showtooltip Redemption
/cast [@mouseover, help, exists][help][@player] Redemption
```

#### Cleanse / dispel

**Cleanse** (`Cleanse`)
```
#showtooltip Cleanse
/cast [@mouseover, help, exists][help][@player] Cleanse
```

**Purify** (`Purify`)
```
#showtooltip Purify
/cast [@mouseover, help, exists][help][@player] Purify
```

#### Wand / auto-attack

**Auto-attack (spam-safe)** (`Attack`)
```
/startattack [@targettarget, harm, exists][harm]
```

#### Buffs

**Blessing of Might** (`BoM`)
```
#showtooltip Blessing of Might
/cast [@mouseover, help, exists][help][@player] Blessing of Might
```

**Blessing of Wisdom** (`BoW`)
```
#showtooltip Blessing of Wisdom
/cast [@mouseover, help, exists][help][@player] Blessing of Wisdom
```

**Blessing of Salvation** (`Salv`)
```
#showtooltip Blessing of Salvation
/cast [@mouseover, help, exists][help][@player] Blessing of Salvation
```

**Blessing of Light** (`BoL`)
```
#showtooltip Blessing of Light
/cast [@mouseover, help, exists][help][@player] Blessing of Light
```

**Greater Blessing of Might** (`GBoM`)
```
#showtooltip Greater Blessing of Might
/cast [@mouseover, help, exists][help][@player] Greater Blessing of Might
```

**Greater Blessing of Wisdom** (`GBoW`)
```
#showtooltip Greater Blessing of Wisdom
/cast [@mouseover, help, exists][help][@player] Greater Blessing of Wisdom
```

**Devotion Aura** (`Devo`)
```
#showtooltip Devotion Aura
/cast Devotion Aura
```

**Retribution Aura** (`RetAura`)
```
#showtooltip Retribution Aura
/cast Retribution Aura
```

**Concentration Aura** (`Conc`)
```
#showtooltip Concentration Aura
/cast Concentration Aura
```

**Blessing of Kings** (`BoK`) — Class spell at level 20 in Forever (was a Protection talent).
```
#showtooltip Blessing of Kings
/cast [@mouseover, help, exists][help][@player] Blessing of Kings
```

#### Panic / defensive

**Divine Shield (press again to cancel)** (`Bubble`) — First press bubbles, second press cancels it early.
```
#showtooltip Divine Shield
/cancelaura Divine Shield
/cast Divine Shield
```

**Divine Protection** (`DivProt`)
```
#showtooltip Divine Protection
/cast Divine Protection
```

**Lay on Hands self** (`LoH me`)
```
#showtooltip Lay on Hands
/cast [@player] Lay on Hands
```

**Blessing of Protection self (press again to cancel)** (`BoP me`) — BoP stops you from attacking, so the second press removes it.
```
#showtooltip Blessing of Protection
/cancelaura Blessing of Protection
/cast [@player] Blessing of Protection
```

**Voice of Truth** (`VoT`) — New in Forever: 6 sec immunity to silence and interrupts. Use before a big heal/cast.
```
#showtooltip Voice of Truth
/cast Voice of Truth
```

#### Class QoL

**Seal of Righteousness** (`SoR`)
```
#showtooltip Seal of Righteousness
/cast Seal of Righteousness
```

**Seal of the Crusader** (`SoCru`)
```
#showtooltip Seal of the Crusader
/cast Seal of the Crusader
```

**Seal of Wisdom** (`SoW`)
```
#showtooltip Seal of Wisdom
/cast Seal of Wisdom
```

**Seal of Light** (`SoL`)
```
#showtooltip Seal of Light
/cast Seal of Light
```

**Seal of Justice** (`SoJ`)
```
#showtooltip Seal of Justice
/cast Seal of Justice
```

**Divine Intervention** (`DI`)
```
#showtooltip Divine Intervention
/cast [@mouseover, help, exists][help][@player] Divine Intervention
```

**Auras on one button** (`Auras`) — Plain click: Devotion. Shift: Concentration. Ctrl: Retribution.
```
#showtooltip [mod:shift] Concentration Aura; [mod:ctrl] Retribution Aura; Devotion Aura
/cast [mod:shift] Concentration Aura; [mod:ctrl] Retribution Aura; Devotion Aura
```

#### Focus

**Hammer of Justice focus** (`HoJ F`)
```
#showtooltip Hammer of Justice
/cast [@focus, harm, exists][harm] Hammer of Justice
```

**Turn Undead focus** (`TU F`)
```
#showtooltip Turn Undead
/cast [@focus, harm, exists][harm] Turn Undead
```

### Paladin — Tank

#### Damage / offensive

**Holy Shield** (`HShield`) — Forever: a 4-charge block buff. Keep it up while tanking.
```
#showtooltip Holy Shield
/cast Holy Shield
```

**Judgement taunt (mouseover)** (`Judge@`) — With Seal of Fury active, Judgement taunts (10 yd). Hover a loose mob to pull it off the healer without changing target.
```
#showtooltip Judgement
/cast [@mouseover, harm, nodead][harm] Judgement
```

#### Buffs

**Seal of Fury** (`SoF`) — New tank seal: Holy damage per hit + absorb shield with a shield equipped. Makes Judgement a taunt.
```
#showtooltip Seal of Fury
/cast Seal of Fury
```

**Righteous Fury** (`RFury`)
```
#showtooltip Righteous Fury
/cast Righteous Fury
```

**Blessing of Sanctuary** (`Sanc`)
```
#showtooltip Blessing of Sanctuary
/cast [@mouseover, help, exists][help][@player] Blessing of Sanctuary
```

#### Panic / defensive

**Templar's Bulwark** (`Bulwark`) — Talent. Absorb shield equal to your max health for 8 sec (5 min cooldown).
```
#showtooltip Templar's Bulwark
/cast Templar's Bulwark
```

#### Focus

**Judgement taunt on focus** (`Judge F`) — With Seal of Fury: taunt your focus (e.g. the add you're watching).
```
#showtooltip Judgement
/cast [@focus, harm, exists][harm] Judgement
```

### Paladin — DPS

#### Damage / offensive

**Repentance** (`Repent`)
```
#showtooltip Repentance
/cast [harm] Repentance
```

#### Buffs

**Sanctity Aura** (`SancAura`)
```
#showtooltip Sanctity Aura
/cast Sanctity Aura
```

**Seal of Command** (`SoCmd`)
```
#showtooltip Seal of Command
/cast Seal of Command
```

#### Class QoL

**Seal swap: Command <> Righteousness** (`Twist`) — Test in beta: with the Twist of Light talent, switching seals lets your next swing also apply the old seal. Swap between swings.
```
#showtooltip
/castsequence Seal of Command, Seal of Righteousness
```

#### Focus

**Repentance focus** (`Repent F`)
```
#showtooltip Repentance
/cast [@focus, harm, exists][harm] Repentance
```

### Paladin — Healer

#### Mouseover healing / utility

**Holy Shock (friend or foe)** (`HShock`) — Heals a friendly mouseover/target, damages an enemy one.
```
#showtooltip Holy Shock
/cast [@mouseover, exists][exists][@player] Holy Shock
```

## Warrior

### Warrior — General (all specs)

#### Damage / offensive

**Heroic Strike / Cleave (Shift)** (`HS/Cleave`) — Click: Heroic Strike. Shift-click: Cleave (level 20).
```
#showtooltip [mod:shift] Cleave; Heroic Strike
/startattack [harm]
/cast [mod:shift, harm] Cleave; [harm] Heroic Strike
```

**Hamstring** (`Ham`)
```
#showtooltip Hamstring
/startattack [harm]
/cast [harm] Hamstring
```

**Slam** (`Slam`) — Level 20 in Forever.
```
#showtooltip Slam
/startattack [harm]
/cast [harm] Slam
```

**Execute** (`Exe`) — Level 24. Target under 20% health; Battle or Berserker Stance.
```
#showtooltip Execute
/startattack [harm]
/cast [harm] Execute
```

**Overpower (to Battle)** (`OP`)
```
#showtooltip Overpower
/startattack [harm]
/cast [nostance:1] Battle Stance; [@targettarget, harm, exists][harm] Overpower
```

**Interrupt (Pummel / Shield Bash)** (`Kick`) — Pummel in Berserker Stance (level 38), Shield Bash in Battle or Defensive (needs a shield). No stance swap: use the stance dance.
```
#showtooltip
/startattack [harm]
/cast [stance:3, harm] Pummel; [harm] Shield Bash
```

#### Wand / auto-attack

**Ranged weapon (Bow/Gun/Crossbow/Thrown)** (`Ranged`) — One button for whatever ranged weapon you have equipped.
```
#showtooltip
/cast [equipped:Thrown] Throw; [equipped:Bows] Shoot Bow; [equipped:Guns] Shoot Gun; [equipped:Crossbows] Shoot Crossbow
```

#### Panic / defensive

**Disarm (to Defensive)** (`Disarm`)
```
#showtooltip Disarm
/cast [nostance:2] Defensive Stance; [@targettarget, harm, exists][harm] Disarm
```

**Stance cooldown (Retaliation/Shield Wall/Recklessness)** (`StanceCD`) — Uses the big cooldown of the stance you're in.
```
#showtooltip [stance:1] Retaliation; [stance:2] Shield Wall; [stance:3] Recklessness
/cast [stance:1] Retaliation; [stance:2] Shield Wall; [stance:3] Recklessness
```

#### Class QoL

**Charge / Intercept (one button)** (`Charge`) — Out of combat: Charge. In combat: Intercept (level 30). Tactical Mastery (now trained) keeps up to 10 rage on a stance swap.
```
#showtooltip Charge
/cast [nocombat, nostance:1] Battle Stance; [nocombat, @targettarget, harm, exists][nocombat, harm] Charge; [nostance:3] Berserker Stance; [@targettarget, harm, exists][harm] Intercept
```

**Charge + Rend (opener)** (`Charge+Rend`) — Charges in (out of combat only) then immediately opens with Rend.
```
#showtooltip Charge
/startattack [harm]
/cast [nocombat, nostance:1] Battle Stance
/cast [nocombat, harm] Charge
/cast [harm] Rend
```

**Taunt (to Defensive)** (`Taunt`) — Target the friend being hit: TT is the mob.
```
#showtooltip Taunt
/cast [nostance:2] Defensive Stance; [@targettarget, harm, exists][harm] Taunt
```

**Mocking Blow (to Battle)** (`Mock`)
```
#showtooltip Mocking Blow
/startattack [harm]
/cast [nostance:1] Battle Stance; [@targettarget, harm, exists][harm] Mocking Blow
```

**Stance dance (Battle -> Defensive -> Berserker)** (`Stances`) — One button cycles Battle -> Defensive -> Berserker -> Battle.
```
#showtooltip Battle Stance
/cast [stance:1] Defensive Stance; [stance:2] Berserker Stance; [stance:3] Battle Stance
```

**Stance toggle (Battle <> Defensive, mods for others)** (`StanceTog`) — Click swaps Battle <> Defensive. Ctrl = Berserker (level 30). Alt = Defensive.
```
#showtooltip
/cast [mod:ctrl, nostance:3] Berserker Stance; [mod:alt, nostance:2] Defensive Stance; [stance:1] Defensive Stance; Battle Stance
```

**Off-hand <> shield swap** (`OHSwap`) — Fill in your own shield and off-hand item names.
```
/equipslot [noequipped:Shields] 17 Your Shield
/equipslot [equipped:Shields] 17 Your Offhand
```

#### Focus

**Interrupt focus (Pummel / Shield Bash)** (`Kick F`) — Interrupts your focus (or your target if you have no focus): Pummel in Berserker Stance, Shield Bash in Battle or Defensive (needs a shield). No stance swap.
```
#showtooltip
/cast [stance:3, @focus, harm, exists][stance:3, harm] Pummel; [@focus, harm, exists][harm] Shield Bash
```

### Warrior — Tank

#### Damage / offensive

**Victory Rush > Revenge > Sunder Armor** (`Rev>Sund`) — One tank spam button: Victory Rush when it's up after a kill, else Revenge when it's lit (after a block, dodge or parry), else Sunder. Use this on trash; the Shield Block version on bosses and big pulls. The last line hides the "not ready" error.
```
#showtooltip
/startattack [harm]
/cast [harm] Victory Rush
/cast [harm] Revenge
/cast [harm] Sunder Armor
/run UIErrorsFrame:Clear()
```

**Shield Block + Revenge > Sunder Armor** (`SBlk+Sund`) — Test in beta: Shield Block has no global cooldown, so it fires with the next button whenever it's off cooldown (needs a shield and Defensive Stance). More blocks = more Revenge procs. Watch your rage: Shield Block 10, Sunder 15.
```
#showtooltip
/startattack [harm]
/cast Shield Block
/cast [harm] Revenge
/cast [harm] Sunder Armor
/run UIErrorsFrame:Clear()
```

**Concussion Blow** (`Concuss`) — Talent (in our level-30 tank build).
```
#showtooltip Concussion Blow
/startattack [harm]
/cast [harm] Concussion Blow
```

**Shield Slam** (`SSlam`) — Talent, level 40. Forever: about double the damage.
```
#showtooltip Shield Slam
/startattack [harm]
/cast [harm] Shield Slam
```

#### Class QoL

**Charge (Vanguard, any stance)** (`VCharge`) — With the Vanguard talent (level-30 tank build) Charge works in Defensive Stance, so no stance swap.
```
#showtooltip Charge
/startattack [harm]
/cast [harm] Charge
```

**Taunt (mouseover)** (`Taunt@`) — Defensive Stance. Hover a loose mob to taunt it without changing target.
```
#showtooltip Taunt
/cast [@mouseover, harm, nodead][harm] Taunt
```

### Warrior — DPS

#### Damage / offensive

**Victory Rush > Heroic Strike** (`VR>HS`) — Test in beta: Victory Rush when it's up after a kill; Heroic Strike (no global cooldown) queues on your next swing either way. Watch your rage.
```
#showtooltip
/startattack [harm]
/cast [harm] Victory Rush
/cast [harm] Heroic Strike
```

**Sweeping Strikes (to Battle)** (`Sweep`) — Arms talent (in our level-30 Arms build). Pair with Cleave.
```
#showtooltip Sweeping Strikes
/cast [nostance:1] Battle Stance; Sweeping Strikes
```

**Mortal Strike** (`MS`) — Arms talent, level 40.
```
#showtooltip Mortal Strike
/startattack [harm]
/cast [harm] Mortal Strike
```

**Bloodthirst** (`BT`) — Fury talent, level 40.
```
#showtooltip Bloodthirst
/startattack [harm]
/cast [harm] Bloodthirst
```

**Whirlwind (to Berserker)** (`WW`) — Level 36.
```
#showtooltip Whirlwind
/cast [nostance:3] Berserker Stance; Whirlwind
```
