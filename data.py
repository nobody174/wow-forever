# =============================================================================
# WoW Forever macro data — single source of truth.
# Edit macros HERE ONLY. Run `python build.py` after any change to regenerate
# macros.html and wow-forever-macros.md.
#
# Layout of this file:
#   1. Macro-string helpers (dps, heal, util, buff, chan, foc, plain, me, stance)
#   2. Small builder helpers (M, G) + macro type labels
#   3. UNIVERSAL  — macros shown on every class (targeting, focus, panic, misc/UI)
#   4. CLASSES    — one block per class, each with a "Shared" section (all specs)
#                   plus one section per spec. One macro per line throughout,
#                   so a single macro can be added/edited/removed without
#                   touching its neighbors.
# =============================================================================

# --- 1. Macro-string helpers ------------------------------------------------
# Each helper returns a ready-to-use macro string (with #showtooltip on line 1
# for anything that actually /cast's a spell) following the user's style rules:
#   dps      -> TT-aware DPS (Priest only): /cast [@targettarget, harm, exists][harm] SPELL
#   dpsHarm  -> plain harm-target DPS (every other class): /cast [harm] SPELL
#   heal     -> mouseover heal/util: /cast [@mouseover, help, exists][help] SPELL
#   util     -> friend-or-foe:       /cast [@mouseover, exists][exists] SPELL
#   buff     -> buff w/ self fallback: /cast [@mouseover, help, exists][help][@player] SPELL
#   chan     -> spam-safe channel:   /cast [...,nochanneling][...,nochanneling] SPELL
#   foc      -> cast on focus:       /cast [@focus, harm, exists][harm] SPELL
#   plain    -> bare cast, no targeting logic
#   me       -> cast on self:        /cast [@player] SPELL
#   stance   -> swap stance then cast (warrior)
#
# Only Priest actually needs target-of-target awareness (dps()) — every other
# class's DPS macros just cast on whatever you have targeted (dpsHarm()).

def dps(spell):
    return f"#showtooltip {spell}\n/cast [@targettarget, harm, exists][harm] {spell}"

def dpsHarm(spell):
    return f"#showtooltip {spell}\n/cast [harm] {spell}"

def heal(spell):
    return f"#showtooltip {spell}\n/cast [@mouseover, help, exists][help] {spell}"

def util(spell):
    return f"#showtooltip {spell}\n/cast [@mouseover, exists][exists] {spell}"

def buff(spell):
    return f"#showtooltip {spell}\n/cast [@mouseover, help, exists][help][@player] {spell}"

def chan(spell):
    return f"#showtooltip {spell}\n/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] {spell}"

def foc(spell):
    return f"#showtooltip {spell}\n/cast [@focus, harm, exists][harm] {spell}"

def plain(spell):
    return f"#showtooltip {spell}\n/cast {spell}"

def me(spell):
    return f"#showtooltip {spell}\n/cast [@player] {spell}"

def stance(required_stance_id, stance_name, spell, tt=True):
    """Swap into `stance_name` if not already in it, then cast `spell`.
    tt=True adds targettarget-aware DPS targeting; tt=False casts with no
    target logic (e.g. self-buffs, AoE like Thunder Clap/Whirlwind)."""
    target = "[@targettarget, harm, exists][harm] " if tt else ""
    return f"#showtooltip {spell}\n/cast [nostance:{required_stance_id}] {stance_name}; {target}{spell}"


# Multi-line macros that don't fit the single-spell helpers above.
WAND = (
    "#showtooltip Shoot\n"
    "/cast [@targettarget, harm, exists, nochanneling:Shoot] Shoot\n"
    "/cast [harm, nochanneling:Shoot] Shoot"
)
MELEE = "/startattack [@targettarget, harm, exists][harm]"
PETATK = "/petattack [@targettarget, harm, exists][harm]"
PETATK_MO = "/petattack [@mouseover, harm, exists][harm]"
PETATK_MO_TT = "/petattack [@mouseover, harm, exists][@targettarget, harm, exists][harm]"
PETATK_SHIFT = (
    "/petfollow [mod:shift]\n"
    "/petattack [nomod:shift, @mouseover, harm, exists][nomod:shift, harm]"
)
PET_ICON_NOTE = ("No #showtooltip: /petattack is not a spell, so it would show a red ?. "
                 "Pick the icon yourself in the macro window: the claw icon from the pet "
                 "bar's Attack button (Ability_GhoulFrenzy).")


# --- 2. Builder helpers + macro type labels ---------------------------------

# Prefix for notes on macros that still need checking in the Forever beta.
BETA = "Test in beta: "

def M(name, code, note=""):
    """One macro entry: display name, macro code, optional short description."""
    return {"name": name, "code": code, "note": note}

def G(kind, macros):
    """One labeled group of macros (e.g. all the DPS macros for a spec)."""
    return {"type": kind, "macros": macros}

# Macro type labels — the 8 original categories plus Misc / UI.
DPS, HEAL, CLEAN, AUTO, BUFF, PANIC, TARGET, QOL, FOCUS, MISC = (
    "Damage / offensive",
    "Mouseover healing / utility",
    "Cleanse / dispel",
    "Wand / auto-attack",
    "Buffs",
    "Panic / defensive",
    "Targeting helpers",
    "Class QoL",
    "Focus",
    "Misc / UI",
)


# =============================================================================
# UNIVERSAL — shown on every class, not spell-specific.
# =============================================================================
UNIVERSAL = [
    G(TARGET, [
        M("Smart target enemy",
          "/targetenemy [noharm][dead]",
          "Only grabs a new enemy if you have no live hostile target."),
        M("Grab TT (take the mob off your friend)",
          "/target [@targettarget, harm, exists]"),
        M("Assist mouseover / friendly target",
          "/assist [@mouseover, help, exists][help]"),
        M("Clear dead target",
          "/cleartarget [dead]"),
        M("Skull mark mouseover / target",
          "/targetmarker [@mouseover, exists][] 8",
          "8 = skull, 7 = cross, 5 = moon, 6 = square. Uses the full /targetmarker "
          "name, not the /tm shorthand — the ThreatMaster addon claims /tm for "
          "itself, which silently breaks this macro if you use the short form."),
    ]),

    G(FOCUS, [
        M("Set focus (mouseover first)", "/focus [@mouseover, exists][]"),
        M("Clear focus", "/clearfocus"),
        M("Target focus", "/target focus"),
        M("Assist focus (set tank as focus)", "/assist focus"),
    ]),

    G(PANIC, [
        M("Healing potion",
          "/use Major Healing Potion",
          "Swap the item name to the potion rank you carry."),
        M("Mana potion",
          "/use Major Mana Potion",
          "Swap the item name to the potion rank you carry."),
    ]),

    G(MISC, [
        M("Zoom out more",
          "/console cameraDistanceMaxZoomFactor 4",
          "Raises the max camera zoom-out distance beyond the default cap."),
        M("Hide guild names",
          "/console UnitNamePlayerGuild 0",
          "Removes guild tags from nameplates and unit frames."),
        M("Hide PvP titles",
          "/console UnitNamePlayerPVPTitle 0",
          "Removes PvP rank titles from nameplates and unit frames."),
        M("Weapon swap: 1H+offhand ↔ 2H",
          "/equipslot 16 Durgen's Crescent Axe\n"
          "/equipslot 17 Veteran Shield\n"
          "/equipslot 16 Ironforge Greathammer",
          "Swap the item names for your own gear. Toggles between 1H+offhand "
          "and 2H each press — slot 16 = main hand, 17 = off hand/shield."),
    ]),
]


# =============================================================================
# CLASSES
# =============================================================================
CLASSES = [


    # -------------------------------------------------------------------- #
    # PRIEST
    # -------------------------------------------------------------------- #
    {"name": "Priest", "color": "#FFFFFF", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Shadow Word: Pain", dps("Shadow Word: Pain")),
                M("Mind Blast", dps("Mind Blast")),
                M("Smite", dps("Smite")),
                M("Holy Fire", dps("Holy Fire")),
                M("Mana Burn", dps("Mana Burn")),
            ]),
            G(AUTO, [
                M("Wand (spam-safe)", WAND),
            ]),
            G(HEAL, [
                M("Flash Heal", heal("Flash Heal")),
                M("Heal", heal("Heal")),
                M("Greater Heal", heal("Greater Heal")),
                M("Lesser Heal", heal("Lesser Heal")),
                M("Renew", heal("Renew")),
                M("Power Word: Shield", heal("Power Word: Shield")),
                M("Prayer of Healing", plain("Prayer of Healing"), "Party-wide, no target needed."),
                M("Resurrection", heal("Resurrection")),
            ]),
            G(CLEAN, [
                M("Dispel Magic (friend or foe)", util("Dispel Magic")),
                M("Cure Disease", heal("Cure Disease")),
                M("Abolish Disease", heal("Abolish Disease")),
            ]),
            G(BUFF, [
                M("Power Word: Fortitude", buff("Power Word: Fortitude")),
                M("Prayer of Fortitude", buff("Prayer of Fortitude")),
                M("Shadow Protection", buff("Shadow Protection")),
                M("Levitate", buff("Levitate")),
                M("Inner Fire", plain("Inner Fire")),
                M("Fear Ward", buff("Fear Ward"), "Racial/availability may differ in Forever."),
            ]),
            G(PANIC, [
                M("Shield self", me("Power Word: Shield")),
                M("Psychic Scream", plain("Psychic Scream")),
                M("Fade", plain("Fade")),
                M("Desperate Prayer", plain("Desperate Prayer"), "Racial priest spell."),
            ]),
            G(FOCUS, [
                M("Shackle Undead on focus", foc("Shackle Undead")),
                M("Mind Control on focus", foc("Mind Control")),
            ]),
        ]},

        {"spec": "Shadow", "groups": [
            G(DPS, [
                M("Mind Flay (spam-safe)", chan("Mind Flay"), "Won't clip an active channel."),
                M("Vampiric Embrace", dps("Vampiric Embrace")),
                M("Silence (interrupt)", "#showtooltip Silence\n/stopcasting\n/cast [@targettarget, harm, exists][harm] Silence",
                  "Clears your current cast first so the interrupt fires instantly."),
                M("Devouring Plague", dps("Devouring Plague"), "Racial priest spell."),
            ]),
            G(BUFF, [
                M("Shadowform (no cancel)",
                  "#showtooltip Shadowform\n/cast [noform] Shadowform",
                  "Won't drop you out of form if pressed again."),
            ]),
            G(FOCUS, [
                M("Silence focus", "#showtooltip Silence\n/stopcasting\n/cast [@focus, harm, exists][harm] Silence",
                  "Clears your current cast first so the interrupt fires instantly."),
            ]),
        ]},

        {"spec": "Holy", "groups": [
            G(HEAL, [
                M("Inner Focus + Greater Heal",
                  "#showtooltip Greater Heal\n/cast Inner Focus\n/cast [@mouseover, help, exists][help] Greater Heal"),
                M("Holy Nova", plain("Holy Nova")),
                M("Prayer of Mending", heal("Prayer of Mending"),
                  "New in Forever. Heals, then jumps to another group member when they take damage."),
                M("Lightwell", plain("Lightwell")),
            ]),
        ]},

        {"spec": "Discipline", "groups": [
            G(HEAL, [
                M("Power Infusion", heal("Power Infusion")),
                M("Penance (friend or foe)", util("Penance"),
                  "New in Forever. Heals a friendly mouseover/target, damages an enemy one."),
                M("Inner Focus + Greater Heal",
                  "#showtooltip Greater Heal\n/cast Inner Focus\n/cast [@mouseover, help, exists][help] Greater Heal"),
            ]),
            G(BUFF, [
                M("Divine Spirit", buff("Divine Spirit")),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # WARLOCK
    # -------------------------------------------------------------------- #
    {"name": "Warlock", "color": "#8788EE", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Shadow Bolt + Imp Firebolt",
                  "#showtooltip Shadow Bolt\n"
                  "/petattack [harm]\n"
                  "/cast [pet:Imp, harm] Firebolt\n"
                  "/cast [harm] Shadow Bolt",
                  "Sends your pet in and, when the Imp is out, fires its Firebolt on the "
                  "same press. Handy if you keep Firebolt autocast off to stop the Imp "
                  "pulling or burning mana. With any other demon the Firebolt line is skipped."),
                M("Corruption", dpsHarm("Corruption")),
                M("Curse of Agony", dpsHarm("Curse of Agony")),
                M("Immolate", dpsHarm("Immolate")),
                M("Searing Pain", dpsHarm("Searing Pain")),
                M("Soul Fire", dpsHarm("Soul Fire")),
                M("Death Coil", dpsHarm("Death Coil")),
                M("Drain Life (spam-safe)", chan("Drain Life")),
                M("Drain Soul (spam-safe)", chan("Drain Soul")),
                M("Drain Mana (spam-safe)", chan("Drain Mana")),
                M("Curse of the Elements", dpsHarm("Curse of the Elements")),
                M("Curse of Shadow", dpsHarm("Curse of Shadow")),
                M("Curse of Recklessness", dpsHarm("Curse of Recklessness")),
                M("Curse of Weakness", dpsHarm("Curse of Weakness")),
                M("Curse of Tongues", dpsHarm("Curse of Tongues")),
                M("Hellfire", plain("Hellfire")),
                M("Rain of Fire", plain("Rain of Fire")),
            ]),
            G(AUTO, [
                M("Wand (spam-safe)", WAND),
            ]),
            G(HEAL, [
                M("Health Funnel (pet)", plain("Health Funnel")),
                M("Unending Breath", buff("Unending Breath")),
                M("Detect Invisibility", buff("Detect Invisibility")),
                M("Soulstone mouseover",
                  "/use [@mouseover, help, exists][help] Major Soulstone",
                  "Swap item name to your soulstone rank."),
            ]),
            G(CLEAN, [
                M("Devour Magic (Felhunter)", heal("Devour Magic")),
            ]),
            G(BUFF, [
                M("Demon Armor", plain("Demon Armor")),
                M("Shadow Ward", plain("Shadow Ward")),
            ]),
            G(PANIC, [
                M("Healthstone", "/use Major Healthstone", "Swap item name to your healthstone rank."),
                M("Howl of Terror", plain("Howl of Terror")),
                M("Fear", dpsHarm("Fear")),
                M("Sacrifice (Voidwalker)", plain("Sacrifice")),
                M("Life Tap", plain("Life Tap")),
            ]),
            G(QOL, [
                M("Pet attack TT / target", PETATK),
                M("Pet follow", "/petfollow"),
                M("Pet passive", "/petpassive"),
                M("Pet defensive", "/petdefensive"),
                M("Spell Lock (Felhunter)", dpsHarm("Spell Lock")),
                M("Torment (Voidwalker taunt)", dpsHarm("Torment")),
                M("Summon Felhunter", plain("Summon Felhunter")),
                M("Summon Voidwalker", plain("Summon Voidwalker")),
                M("Summon Succubus", plain("Summon Succubus")),
                M("Summon Imp", plain("Summon Imp")),
            ]),
            G(FOCUS, [
                M("Fear focus", foc("Fear")),
                M("Banish focus", foc("Banish")),
                M("Seduction focus", foc("Seduction")),
                M("Spell Lock focus", foc("Spell Lock")),
                M("Enslave Demon focus", foc("Enslave Demon")),
                M("Bane of Havoc focus", foc("Bane of Havoc"),
                  "New in Forever. Put it on a second mob (focus), then nuke your target: "
                  "part of your damage is copied onto the focus."),
            ]),
        ]},

        {"spec": "Affliction", "groups": [
            G(DPS, [
                M("Siphon Life", dpsHarm("Siphon Life")),
                M("Curse of Exhaustion", dpsHarm("Curse of Exhaustion")),
                M("Wrack (spam-safe)", chan("Wrack"),
                  "New in Forever. Channeled drain that makes the target take more Shadow DoT damage."),
                M("Amplify Curse + Agony",
                  "#showtooltip Curse of Agony\n/cast Amplify Curse\n/cast [harm] Curse of Agony"),
                M("DoT sequence (press to roll dots)",
                  "#showtooltip Corruption\n"
                  "/castsequence [harm] reset=target Corruption, Curse of Agony, Siphon Life, Immolate"),
            ]),
            G(PANIC, [
                M("Dark Pact", plain("Dark Pact"),
                  BETA + "not seen in the Forever beta talent tree, may be removed."),
            ]),
        ]},

        {"spec": "Demonology", "groups": [
            G(QOL, [
                M("Fel Domination + Felhunter",
                  "#showtooltip Summon Felhunter\n/cast Fel Domination\n/cast Summon Felhunter"),
                M("Fel Domination + Voidwalker",
                  "#showtooltip Summon Voidwalker\n/cast Fel Domination\n/cast Summon Voidwalker"),
                M("Soul Link", plain("Soul Link")),
                M("Demonic Sacrifice", plain("Demonic Sacrifice")),
            ]),
        ]},

        {"spec": "Destruction", "groups": [
            G(DPS, [
                M("Conflagrate", dpsHarm("Conflagrate")),
                M("Shadowburn", dpsHarm("Shadowburn")),
                M("Incinerate", dpsHarm("Incinerate"),
                  "New in Forever. Hits harder when Immolate is on the target."),
                M("Immolate > Conflagrate",
                  "#showtooltip Immolate\n"
                  "/castsequence [harm] reset=target/10 Immolate, Conflagrate"),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # MAGE
    # -------------------------------------------------------------------- #
    {"name": "Mage", "color": "#69CCF0", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Frostbolt", dpsHarm("Frostbolt")),
                M("Fireball", dpsHarm("Fireball")),
                M("Arcane Missiles (spam-safe)", chan("Arcane Missiles")),
                M("Arcane Explosion", plain("Arcane Explosion")),
                M("Fire Blast", dpsHarm("Fire Blast")),
                M("Frost Nova", "#showtooltip Frost Nova\n/stopcasting\n/cast [harm] Frost Nova",
                  "Clears your current cast first so the root fires instantly."),
                M("Cone of Cold", plain("Cone of Cold")),
                M("Scorch", dpsHarm("Scorch")),
                M("Counterspell (interrupt)", "#showtooltip Counterspell\n/stopcasting\n/cast [harm] Counterspell",
                  "Clears your current cast first so the interrupt fires instantly."),
                M("Polymorph", dpsHarm("Polymorph")),
                M("Polymorph + Diamond mark",
                  "#showtooltip Polymorph\n/targetmarker [harm] 3\n/cast [harm] Polymorph",
                  "Marks the sheep target with a diamond so the group knows not to break it. "
                  "Uses the full /targetmarker name, not /tm — the ThreatMaster addon claims "
                  "/tm for itself, which silently breaks this macro if you use the short form."),
            ]),
            G(HEAL, [
                M("Mana Shield", plain("Mana Shield")),
            ]),
            G(BUFF, [
                M("Arcane Intellect", buff("Arcane Intellect")),
                M("Frost Armor", plain("Frost Armor")),
                M("Ice Armor", plain("Ice Armor")),
                M("Molten Armor", plain("Molten Armor")),
                M("Dampen Magic", buff("Dampen Magic")),
                M("Amplify Magic", buff("Amplify Magic")),
            ]),
            G(PANIC, [
                M("Ice Block (press again to cancel)",
                  "#showtooltip Ice Block\n/cancelaura Ice Block\n/cast Ice Block",
                  "First press casts Ice Block, second press cancels it early."),
                M("Blink", plain("Blink")),
                M("Evocation", plain("Evocation")),
            ]),
            G(QOL, [
                M("Conjure Food", plain("Conjure Food")),
                M("Conjure Water", plain("Conjure Water")),
                M("Summon Water Elemental", plain("Summon Water Elemental")),
                M("Remove Curse", heal("Remove Curse")),
            ]),
            G(CLEAN, [
                M("Remove Curse (friend or foe)", util("Remove Curse")),
            ]),
            G(FOCUS, [
                M("Counterspell focus", "#showtooltip Counterspell\n/stopcasting\n/cast [@focus, harm, exists][harm] Counterspell",
                  "Clears your current cast first so the interrupt fires instantly."),
                M("Polymorph focus", foc("Polymorph")),
            ]),
        ]},

        {"spec": "Arcane", "groups": [
            G(DPS, [
                M("Arcane Power + Arcane Missiles", "#showtooltip Arcane Missiles\n/cast Arcane Power\n/cast [harm] Arcane Missiles"),
                M("Presence of Mind + Frostbolt", "#showtooltip Frostbolt\n/cast Presence of Mind\n/cast [harm] Frostbolt", "Instant-cast next spell."),
                M("Presence of Mind + Pyroblast", "#showtooltip Pyroblast\n/cast Presence of Mind\n/cast [harm] Pyroblast",
                  "The classic burst combo for Arcane/Fire hybrids: instant Pyroblast."),
                M("Arcane Blast", dpsHarm("Arcane Blast"),
                  "New in Forever. Each cast in a row costs more and powers up your next other spell."),
            ]),
        ]},

        {"spec": "Fire", "groups": [
            G(DPS, [
                M("Combustion", plain("Combustion")),
                M("Pyroblast", dpsHarm("Pyroblast")),
            ]),
        ]},

        {"spec": "Frost", "groups": [
            G(DPS, [
                M("Ice Lance", dpsHarm("Ice Lance")),
                M("Cold Snap", plain("Cold Snap")),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # ROGUE
    # -------------------------------------------------------------------- #
    {"name": "Rogue", "color": "#FFF569", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Sinister Strike", dpsHarm("Sinister Strike")),
                M("Backstab", dpsHarm("Backstab")),
                M("Eviscerate", dpsHarm("Eviscerate")),
                M("Gouge", dpsHarm("Gouge")),
                M("Kidney Shot", dpsHarm("Kidney Shot")),
                M("Rupture", dpsHarm("Rupture")),
                M("Garrote", dpsHarm("Garrote"), "Requires stealth."),
                M("Ambush", dpsHarm("Ambush"), "Requires stealth."),
                M("Cheap Shot", dpsHarm("Cheap Shot"), "Requires stealth. Classic stunlock opener."),
                M("Expose Armor", dpsHarm("Expose Armor")),
                M("Sap", dpsHarm("Sap"), "Only works on an out-of-combat target."),
                M("Kick (interrupt)", "#showtooltip Kick\n/stopcasting\n/cast [harm] Kick",
                  "Clears your current cast first so the interrupt fires instantly."),
            ]),
            G(AUTO, [
                M("Auto-attack (spam-safe)", MELEE),
            ]),
            G(BUFF, [
                M("Slice and Dice", plain("Slice and Dice")),
            ]),
            G(PANIC, [
                M("Evasion", plain("Evasion")),
                M("Vanish", plain("Vanish")),
                M("Sprint", plain("Sprint")),
                M("Blind", dpsHarm("Blind")),
            ]),
            G(QOL, [
                M("Stealth (no cancel)", "#showtooltip Stealth\n/cast [nostealth] Stealth", "Won't drop you out of stealth if pressed again."),
                M("Pick Lock", plain("Pick Lock")),
                M("Pick Pocket", dpsHarm("Pick Pocket")),
                M("Pick Pocket + Sap",
                  "#showtooltip Sap\n/cast [harm] Pick Pocket\n/cast [harm] Sap",
                  "Pick Pocket has no global cooldown, so one press robs and saps."),
                M("Apply poison to main hand", "/use Instant Poison\n/use Main Hand Weapon", "Swap the item name to the poison you carry."),
                M("Apply poison to off hand", "/use Deadly Poison\n/use Off Hand Weapon", "Swap the item name to the poison you carry."),
                M("Distract", dpsHarm("Distract")),
                M("Feint", dpsHarm("Feint")),
            ]),
            G(CLEAN, [
                M("No dispel", "", "Rogues have no dispel. Interrupt instead with Kick, or silence with Gouge/Kidney Shot/Blind."),
            ]),
            G(FOCUS, [
                M("Kick focus", "#showtooltip Kick\n/stopcasting\n/cast [@focus, harm, exists][harm] Kick",
                  "Clears your current cast first so the interrupt fires instantly."),
                M("Kidney Shot focus", foc("Kidney Shot")),
                M("Blind focus", foc("Blind")),
            ]),
        ]},

        {"spec": "Assassination", "groups": [
            G(DPS, [
                M("Venom", dpsHarm("Venom"),
                  "Forever's finisher (replaces Envenom): boosts poison damage and proc chance. "
                  "Longer duration per combo point."),
                M("Mutilate", dpsHarm("Mutilate")),
                M("Cold Blood + Ambush", "#showtooltip Ambush\n/cast Cold Blood\n/cast [harm] Ambush", "Requires stealth."),
            ]),
        ]},

        {"spec": "Combat", "groups": [
            G(DPS, [
                M("Blade Flurry", plain("Blade Flurry")),
                M("Adrenaline Rush", plain("Adrenaline Rush")),
            ]),
        ]},

        {"spec": "Subtlety", "groups": [
            G(DPS, [
                M("Hemorrhage", dpsHarm("Hemorrhage")),
                M("Premeditation", plain("Premeditation"), "Requires stealth."),
            ]),
            G(PANIC, [
                M("Cloak of Shadows", plain("Cloak of Shadows")),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # SHAMAN
    # -------------------------------------------------------------------- #
    {"name": "Shaman", "color": "#0070DE", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Lightning Bolt", dpsHarm("Lightning Bolt")),
                M("Chain Lightning", dpsHarm("Chain Lightning")),
                M("Earth Shock (interrupt)", "#showtooltip Earth Shock\n/stopcasting\n/cast [harm] Earth Shock",
                  "Clears your current cast first so the interrupt fires instantly."),
                M("Flame Shock", dpsHarm("Flame Shock")),
                M("Frost Shock", dpsHarm("Frost Shock")),
                M("Purge (offensive dispel)", dpsHarm("Purge")),
            ]),
            G(AUTO, [
                M("Auto-attack (spam-safe)", MELEE),
            ]),
            G(HEAL, [
                M("Healing Wave", heal("Healing Wave")),
                M("Lesser Healing Wave", heal("Lesser Healing Wave")),
                M("Chain Heal", heal("Chain Heal")),
                M("Ancestral Spirit", heal("Ancestral Spirit")),
                M("Riptide", heal("Riptide"),
                  "New in Forever. Instant heal + HoT that boosts your next Chain Heal."),
            ]),
            G(CLEAN, [
                M("Cure Poison", heal("Cure Poison")),
                M("Cure Disease", heal("Cure Disease")),
            ]),
            G(BUFF, [
                M("Lightning Shield", plain("Lightning Shield")),
                M("Water Shield", plain("Water Shield"),
                  "New in Forever. Mana back when you're hit or crit-heal. Replaces Lightning Shield for healers."),
                M("Rockbiter Weapon", plain("Rockbiter Weapon")),
                M("Flametongue Weapon", plain("Flametongue Weapon")),
                M("Frostbrand Weapon", plain("Frostbrand Weapon")),
                M("Water Walking", buff("Water Walking")),
                M("Water Breathing", buff("Water Breathing")),
            ]),
            G(PANIC, [
                M("Self Lesser Healing Wave", me("Lesser Healing Wave")),
                M("Stoneclaw Totem", plain("Stoneclaw Totem")),
                M("Grounding Totem", plain("Grounding Totem")),
                M("Ghost Wolf (no cancel)", "#showtooltip Ghost Wolf\n/cast [noform] Ghost Wolf"),
            ]),
            G(QOL, [
                M("Totems: melee group (press 4x)",
                  "#showtooltip Strength of Earth Totem\n"
                  "/castsequence reset=combat Strength of Earth Totem, Windfury Totem, Searing Totem, Mana Spring Totem"),
                M("Totems: caster group (press 4x)",
                  "#showtooltip Stoneskin Totem\n"
                  "/castsequence reset=combat Stoneskin Totem, Grace of Air Totem, Searing Totem, Mana Spring Totem",
                  "Swap Grace of Air for Tranquil Air if you prefer."),
                M("Tremor Totem", plain("Tremor Totem")),
                M("Poison Cleansing Totem", plain("Poison Cleansing Totem")),
                M("Disease Cleansing Totem", plain("Disease Cleansing Totem")),
                M("Earthbind Totem", plain("Earthbind Totem")),
                M("Magma Totem", plain("Magma Totem")),
                M("Fire Nova Totem", plain("Fire Nova Totem")),
                M("Healing Stream Totem", plain("Healing Stream Totem")),
            ]),
            G(FOCUS, [
                M("Earth Shock interrupt on focus", "#showtooltip Earth Shock\n/stopcasting\n/cast [@focus, harm, exists][harm] Earth Shock",
                  "Clears your current cast first so the interrupt fires instantly."),
                M("Purge focus", foc("Purge")),
            ]),
        ]},

        {"spec": "Elemental", "groups": [
            G(DPS, [
                M("Lava Burst", dpsHarm("Lava Burst"),
                  "New in Forever. Hits 20% harder with your Flame Shock on the target."),
                M("Flame Shock > Lava Burst",
                  "#showtooltip Flame Shock\n/castsequence [harm] reset=target/12 Flame Shock, Lava Burst",
                  "Opener: Flame Shock, then the boosted Lava Burst."),
                M("Elemental Mastery + Chain Lightning",
                  "#showtooltip Chain Lightning\n/cast Elemental Mastery\n/cast [harm] Chain Lightning",
                  BETA + "Elemental Mastery was not seen in the Forever beta talent tree."),
                M("Elemental Mastery + Lightning Bolt",
                  "#showtooltip Lightning Bolt\n/cast Elemental Mastery\n/cast [harm] Lightning Bolt",
                  BETA + "Elemental Mastery was not seen in the Forever beta talent tree."),
            ]),
        ]},

        {"spec": "Enhancement", "groups": [
            G(DPS, [
                M("Stormstrike", dpsHarm("Stormstrike"),
                  "Also starts auto-attack. In Forever it boosts only your NEXT Lightning Bolt, "
                  "Chain Lightning or Earth Shock, so follow up with one."),
            ]),
            G(BUFF, [
                M("Windfury Weapon", plain("Windfury Weapon")),
                M("Windfury Weapon + Lightning Shield refresh",
                  "#showtooltip Lightning Shield\n/castsequence reset=2 Lightning Shield, Windfury Weapon",
                  "Press twice to reapply both buffs; resets after 2 sec so it doesn't get stuck mid-sequence."),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # HUNTER
    # -------------------------------------------------------------------- #
    {"name": "Hunter", "color": "#ABD473", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Hunter's Mark", dpsHarm("Hunter's Mark")),
                M("Hunter's Mark + send pet (opener)",
                  "#showtooltip Hunter's Mark\n/petattack [harm]\n/cast [harm] Hunter's Mark",
                  "One press marks the target and sends the pet in."),
                M("Serpent Sting", dpsHarm("Serpent Sting")),
                M("Arcane Shot", dpsHarm("Arcane Shot")),
                M("Multi-Shot", dpsHarm("Multi-Shot"),
                  "Forever: 0.5 sec cast, 6 sec cooldown. Stand still for it."),
                M("Volley at cursor", "#showtooltip Volley\n/cast [@cursor] Volley",
                  "Forever removed Volley's cooldown, so it's a real AoE button now. "
                  "Drops at your mouse cursor, no targeting circle."),
                M("Concussive Shot", dpsHarm("Concussive Shot")),
                M("Viper Sting", dpsHarm("Viper Sting")),
                M("Scorpid Sting", dpsHarm("Scorpid Sting")),
                M("Raptor Strike + Wing Clip",
                  "#showtooltip Raptor Strike\n/cast [harm] Raptor Strike\n/cast [harm] Wing Clip"),
                M("Mongoose Bite", dpsHarm("Mongoose Bite")),
                M("Raptor Strike + Mongoose Bite + Wing Clip (test — GCD may skip some)",
                  "#showtooltip Raptor Strike\n/cast [harm] Raptor Strike\n/cast [harm] Mongoose Bite\n/cast [harm] Wing Clip",
                  "Experimental 3-in-1. Only the first ability that both fires and consumes the GCD will actually go off per press — likely to just spam Raptor Strike. Testing to see how WoW Forever's client handles the fallthrough."),
                M("Wing Clip", dpsHarm("Wing Clip")),
                M("Distracting Shot", dpsHarm("Distracting Shot")),
                M("Tranquilizing Shot (enrage dispel)",
                  dpsHarm("Tranquilizing Shot"),
                  "Hunter's only dispel: removes Frenzy from enemies."),
            ]),
            G(AUTO, [
                M("Auto Shot (spam-safe)",
                  "#showtooltip Auto Shot\n/cast [@targettarget, harm, exists][harm] !Auto Shot",
                  "Hunter exception: ! stops Auto Shot toggling off. Unlike wand Shoot, it works here."),
                M("Melee auto-attack", MELEE),
            ]),
            G(BUFF, [
                M("Aspect: Hawk in combat, Cheetah out",
                  "#showtooltip Aspect of the Hawk\n/cast [combat] Aspect of the Hawk; Aspect of the Cheetah"),
                M("Aspect toggle: Cheetah ↔ Hawk",
                  "#showtooltip\n/castsequence reset=combat Aspect of the Cheetah, Aspect of the Hawk",
                  "Each press swaps to the other aspect; the icon shows the next one. "
                  "Resets after combat, so the first press after a fight is always Cheetah. "
                  "Cheetah dazes you when hit, so press again before pulling."),
                M("Aspect of the Hawk", plain("Aspect of the Hawk")),
                M("Aspect of the Monkey", plain("Aspect of the Monkey")),
                M("Aspect of the Pack", plain("Aspect of the Pack")),
                M("Aspect of the Wild", plain("Aspect of the Wild")),
            ]),
            G(PANIC, [
                M("Feign Death (clean)",
                  "#showtooltip Feign Death\n/petfollow\n/stopattack\n/cast Feign Death",
                  "Calls the pet back and stops attacking first, so the pet doesn't keep mobs on you."),
                M("Disengage", dpsHarm("Disengage")),
                M("Freezing Trap", plain("Freezing Trap")),
                M("Frost Trap", plain("Frost Trap")),
                M("Rapid Fire", plain("Rapid Fire")),
            ]),
            G(QOL, [
                M("Pet attack TT / target", PETATK),
                M("Pet attack mouseover", PETATK_MO,
                  "Attacks the enemy under your mouse, else your target. " + PET_ICON_NOTE),
                M("Pet attack mouseover / TT", PETATK_MO_TT,
                  "Mouseover first, then your target's target, then your target. " + PET_ICON_NOTE),
                M("Pet attack / Shift = follow", PETATK_SHIFT,
                  "Press to send the pet (mouseover first); Shift+press calls it back. " + PET_ICON_NOTE),
                M("Pet follow", "/petfollow"),
                M("Pet passive", "/petpassive"),
                M("Call / Revive / Mend (one button)",
                  "#showtooltip Mend Pet\n/cast [nopet] Call Pet; [@pet, dead] Revive Pet; Mend Pet"),
                M("Feed Pet",
                  "#showtooltip Feed Pet\n/cast Feed Pet\n/use Tough Jerky",
                  "Swap food item for your pet's diet."),
                M("Flare", plain("Flare")),
                M("Explosive Trap", plain("Explosive Trap")),
                M("Immolation Trap", plain("Immolation Trap")),
            ]),
            G(CLEAN, [
                M("No friendly dispel", "",
                  "Hunters have no friendly cleanse. Use Tranquilizing Shot (Damage / offensive) instead."),
            ]),
            G(FOCUS, [
                M("Hunter's Mark focus", foc("Hunter's Mark")),
                M("Concussive Shot focus", foc("Concussive Shot")),
            ]),
        ]},

        {"spec": "Beast Mastery", "groups": [
            G(DPS, [
                M("Bestial Wrath + Rapid Fire burst",
                  "#showtooltip Bestial Wrath\n/cast Bestial Wrath\n/cast Rapid Fire"),
                M("Intimidation + pet attack",
                  "#showtooltip Intimidation\n/petattack [harm]\n/cast Intimidation",
                  "Intimidation only fires on the pet's next hit, so this sends the pet in too."),
            ]),
        ]},

        {"spec": "Marksmanship", "groups": [
            G(DPS, [
                M("Aimed Shot", dpsHarm("Aimed Shot")),
                M("Scatter Shot", dpsHarm("Scatter Shot")),
            ]),
            G(BUFF, [
                M("Trueshot Aura", plain("Trueshot Aura")),
            ]),
            G(FOCUS, [
                M("Scatter Shot focus", foc("Scatter Shot")),
            ]),
        ]},

        {"spec": "Survival", "groups": [
            G(DPS, [
                M("Counterattack", dpsHarm("Counterattack")),
            ]),
            G(PANIC, [
                M("Deterrence", plain("Deterrence")),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # PALADIN
    # -------------------------------------------------------------------- #
    {"name": "Paladin", "color": "#F58CBA", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Holy Strike + auto-attack",
                  "#showtooltip Holy Strike\n/startattack [harm]\n/cast [harm] Holy Strike",
                  "New baseline strike in Forever (level 6, 12 sec cooldown)."),
                M("Judgement", dpsHarm("Judgement"),
                  "Forever: Judgement no longer uses up your seal, so no reseal needed."),
                M("Hammer of Wrath", dpsHarm("Hammer of Wrath")),
                M("Exorcism", dpsHarm("Exorcism")),
                M("Hammer of Justice", dpsHarm("Hammer of Justice")),
                M("Consecration", plain("Consecration")),
                M("Holy Wrath", plain("Holy Wrath")),
            ]),
            G(AUTO, [
                M("Auto-attack (spam-safe)", MELEE),
            ]),
            G(HEAL, [
                M("Holy Light", heal("Holy Light")),
                M("Flash of Light", heal("Flash of Light")),
                M("Lay on Hands", heal("Lay on Hands")),
                M("Blessing of Protection", heal("Blessing of Protection")),
                M("Blessing of Freedom", heal("Blessing of Freedom")),
                M("Redemption", heal("Redemption")),
            ]),
            G(CLEAN, [
                M("Cleanse", heal("Cleanse")),
                M("Purify", heal("Purify")),
            ]),
            G(BUFF, [
                M("Blessing of Might", buff("Blessing of Might")),
                M("Blessing of Wisdom", buff("Blessing of Wisdom")),
                M("Blessing of Salvation", buff("Blessing of Salvation")),
                M("Blessing of Light", buff("Blessing of Light")),
                M("Greater Blessing of Might", buff("Greater Blessing of Might")),
                M("Greater Blessing of Wisdom", buff("Greater Blessing of Wisdom")),
                M("Devotion Aura", plain("Devotion Aura")),
                M("Retribution Aura", plain("Retribution Aura")),
                M("Concentration Aura", plain("Concentration Aura")),
                M("Blessing of Kings", buff("Blessing of Kings"),
                  "Class spell at level 20 in Forever (was a Protection talent)."),
            ]),
            G(PANIC, [
                M("Divine Shield (press again to cancel)",
                  "#showtooltip Divine Shield\n/cancelaura Divine Shield\n/cast Divine Shield",
                  "First press bubbles, second press cancels it early."),
                M("Divine Protection", plain("Divine Protection")),
                M("Lay on Hands self", me("Lay on Hands")),
                M("Blessing of Protection self (press again to cancel)",
                  "#showtooltip Blessing of Protection\n/cancelaura Blessing of Protection\n/cast [@player] Blessing of Protection",
                  "BoP stops you from attacking, so the second press removes it."),
                M("Voice of Truth", plain("Voice of Truth"),
                  "New in Forever: 6 sec immunity to silence and interrupts. Use before a big heal/cast."),
            ]),
            G(QOL, [
                M("Seal of Righteousness", plain("Seal of Righteousness")),
                M("Seal of the Crusader", plain("Seal of the Crusader")),
                M("Seal of Wisdom", plain("Seal of Wisdom")),
                M("Seal of Light", plain("Seal of Light")),
                M("Seal of Justice", plain("Seal of Justice")),
                M("Divine Intervention", heal("Divine Intervention")),
            ]),
            G(FOCUS, [
                M("Hammer of Justice focus", foc("Hammer of Justice")),
                M("Turn Undead focus", foc("Turn Undead")),
            ]),
        ]},

        {"spec": "Retribution", "groups": [
            G(DPS, [
                M("Repentance", dpsHarm("Repentance")),
            ]),
            G(BUFF, [
                M("Sanctity Aura", plain("Sanctity Aura")),
                M("Seal of Command", plain("Seal of Command")),
            ]),
            G(QOL, [
                M("Seal swap: Command <> Righteousness",
                  "#showtooltip\n/castsequence Seal of Command, Seal of Righteousness",
                  BETA + "with the Twist of Light talent, switching seals lets your next swing "
                  "also apply the old seal. Swap between swings."),
            ]),
            G(FOCUS, [
                M("Repentance focus", foc("Repentance")),
            ]),
        ]},

        {"spec": "Holy", "groups": [
            G(HEAL, [
                M("Holy Shock (friend or foe)", util("Holy Shock"),
                  "Heals a friendly mouseover/target, damages an enemy one."),
            ]),
        ]},

        {"spec": "Protection", "groups": [
            G(DPS, [
                M("Holy Shield", plain("Holy Shield"),
                  "Forever: a 4-charge block buff. Keep it up while tanking."),
                M("Judgement taunt (mouseover)",
                  "#showtooltip Judgement\n/cast [@mouseover, harm, nodead][harm] Judgement",
                  "With Seal of Fury active, Judgement taunts (10 yd). Hover a loose mob to "
                  "pull it off the healer without changing target."),
            ]),
            G(BUFF, [
                M("Seal of Fury", plain("Seal of Fury"),
                  "New tank seal: Holy damage per hit + absorb shield with a shield equipped. "
                  "Makes Judgement a taunt."),
                M("Righteous Fury", plain("Righteous Fury")),
                M("Blessing of Sanctuary", buff("Blessing of Sanctuary")),
            ]),
            G(PANIC, [
                M("Templar's Bulwark", plain("Templar's Bulwark"),
                  "Talent. Absorb shield equal to your max health for 8 sec (5 min cooldown)."),
            ]),
            G(FOCUS, [
                M("Judgement taunt on focus", foc("Judgement"),
                  "With Seal of Fury: taunt your focus (e.g. the add you're watching)."),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # WARRIOR
    # -------------------------------------------------------------------- #
    {"name": "Warrior", "color": "#C79C6E", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Heroic Strike", dpsHarm("Heroic Strike")),
                M("Cleave", dpsHarm("Cleave")),
                M("Rend", dpsHarm("Rend")),
                M("Hamstring", dpsHarm("Hamstring")),
                M("Sunder Armor", dpsHarm("Sunder Armor")),
                M("Execute", dpsHarm("Execute")),
                M("Overpower (to Battle)", stance(1, "Battle Stance", "Overpower")),
                M("Demoralizing Shout", plain("Demoralizing Shout")),
                M("Thunder Clap (to Battle)", stance(1, "Battle Stance", "Thunder Clap", tt=False)),
            ]),
            G(AUTO, [
                M("Auto-attack (spam-safe)", MELEE),
            ]),
            G(BUFF, [
                M("Battle Shout", plain("Battle Shout")),
                M("Bloodrage", plain("Bloodrage")),
                M("Berserker Rage (to Berserker)", stance(3, "Berserker Stance", "Berserker Rage", tt=False)),
            ]),
            G(PANIC, [
                M("Shield Wall (to Defensive)", stance(2, "Defensive Stance", "Shield Wall", tt=False)),
                M("Retaliation (to Battle)", stance(1, "Battle Stance", "Retaliation", tt=False)),
                M("Intimidating Shout", dpsHarm("Intimidating Shout")),
                M("Disarm (to Defensive)", stance(2, "Defensive Stance", "Disarm")),
            ]),
            G(QOL, [
                M("Battle Stance", plain("Battle Stance")),
                M("Defensive Stance", plain("Defensive Stance")),
                M("Berserker Stance", plain("Berserker Stance")),
                M("Charge / Intercept (one button)",
                  "#showtooltip Charge\n"
                  "/cast [nocombat, nostance:1] Battle Stance; "
                  "[nocombat, @targettarget, harm, exists][nocombat, harm] Charge; "
                  "[nostance:3] Berserker Stance; "
                  "[@targettarget, harm, exists][harm] Intercept",
                  "Out of combat: Charge. In combat: Intercept. Stance swaps cost rage above your Tactical Mastery cap."),
                M("Taunt (to Defensive)", stance(2, "Defensive Stance", "Taunt"), "Target the friend being hit: TT is the mob."),
                M("Mocking Blow (to Battle)", stance(1, "Battle Stance", "Mocking Blow")),
                M("Challenging Shout", plain("Challenging Shout")),
                M("Charge + Rend (opener)",
                  "#showtooltip Charge\n"
                  "/cast [nocombat, nostance:1] Battle Stance\n"
                  "/cast [nocombat, harm] Charge\n"
                  "/cast [harm] Rend",
                  "Charges in (out of combat only) then immediately opens with Rend."),
                M("Stance dance (Battle -> Defensive -> Berserker)",
                  "#showtooltip Battle Stance\n"
                  "/cast [stance:1] Defensive Stance; [stance:2] Berserker Stance; [stance:3] Battle Stance",
                  "One button cycles Battle -> Defensive -> Berserker -> Battle."),
            ]),
            G(CLEAN, [
                M("No dispel", "", "Warriors have no dispel. Interrupt instead with Pummel or Shield Bash."),
            ]),
            G(FOCUS, [
                M("Pummel focus", "#showtooltip Pummel\n/cast [nostance:3] Berserker Stance; [@focus, harm, exists][harm] Pummel"),
                M("Shield Bash focus", foc("Shield Bash")),
                M("Taunt focus", foc("Taunt")),
            ]),
        ]},

        {"spec": "Fury", "groups": [
            G(DPS, [
                M("Bloodthirst", dpsHarm("Bloodthirst")),
                M("Whirlwind (to Berserker)", stance(3, "Berserker Stance", "Whirlwind", tt=False)),
                M("Pummel (to Berserker)", stance(3, "Berserker Stance", "Pummel")),
                M("Slam", dpsHarm("Slam")),
                M("Piercing Howl", plain("Piercing Howl")),
            ]),
            G(BUFF, [
                M("Death Wish", plain("Death Wish")),
                M("Recklessness (to Berserker)", stance(3, "Berserker Stance", "Recklessness", tt=False)),
            ]),
        ]},

        {"spec": "Protection", "groups": [
            G(DPS, [
                M("Shield Slam", dpsHarm("Shield Slam")),
                M("Sunder + Heroic Strike",
                  "#showtooltip Sunder Armor\n/cast [harm] Heroic Strike\n/cast [harm] Sunder Armor",
                  "Heroic Strike has no global cooldown (it queues on your next swing), "
                  "so it rides along with Sunder. Watch your rage."),
                M("Revenge", dpsHarm("Revenge")),
                M("Shield Bash", dpsHarm("Shield Bash")),
                M("Concussion Blow", dpsHarm("Concussion Blow")),
            ]),
            G(PANIC, [
                M("Shield Block", plain("Shield Block")),
                M("Last Stand", plain("Last Stand")),
            ]),
        ]},
    ]},
]
