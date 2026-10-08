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
#   dpsMO    -> mouseover-harm w/ target fallback: /cast [@mouseover, harm, exists][harm] SPELL
#              (hit whatever's under your mouse without changing your actual
#              target; falls back to your target if nothing's under the mouse)
#   heal     -> mouseover heal w/ self fallback: /cast [@mouseover, help, exists][help][@player] SPELL
#   util     -> friend-or-foe w/ self fallback:  /cast [@mouseover, exists][exists][@player] SPELL
#   buff     -> buff w/ self fallback: /cast [@mouseover, help, exists][help][@player] SPELL
#   chan     -> spam-safe channel:   /cast [...,nochanneling][...,nochanneling] SPELL
#   melee    -> /startattack + [harm] cast (melee strikes)
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

def dpsMO(spell):
    return f"#showtooltip {spell}\n/cast [@mouseover, harm, exists][harm] {spell}"

def heal(spell):
    return f"#showtooltip {spell}\n/cast [@mouseover, help, exists][help][@player] {spell}"

def util(spell):
    return f"#showtooltip {spell}\n/cast [@mouseover, exists][exists][@player] {spell}"

def buff(spell):
    return f"#showtooltip {spell}\n/cast [@mouseover, help, exists][help][@player] {spell}"

def chan(spell):
    return f"#showtooltip {spell}\n/cast [@targettarget, harm, exists, nochanneling][harm, nochanneling] {spell}"

def melee(spell):
    """Melee strike that also turns on auto-attack (spam-safe /startattack)."""
    return f"#showtooltip {spell}\n/startattack [harm]\n/cast [harm] {spell}"

def foc(spell):
    return f"#showtooltip {spell}\n/cast [@focus, harm, exists][harm] {spell}"

def plain(spell):
    return f"#showtooltip {spell}\n/cast {spell}"

def me(spell):
    return f"#showtooltip {spell}\n/cast [@player] {spell}"

def stance(required_stance_id, stance_name, spell, tt=True, attack=False):
    """Swap into `stance_name` if not already in it, then cast `spell`.
    tt=True adds targettarget-aware DPS targeting; tt=False casts with no
    target logic (e.g. self-buffs, AoE like Thunder Clap/Whirlwind).
    attack=True adds a /startattack [harm] line (melee strikes)."""
    target = "[@targettarget, harm, exists][harm] " if tt else ""
    start = "/startattack [harm]\n" if attack else ""
    return f"#showtooltip {spell}\n{start}/cast [nostance:{required_stance_id}] {stance_name}; {target}{spell}"


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

def M(name, code, note="", short=None, icon=None):
    """One macro entry: display name, macro code, optional short description,
    in-game short name (max 16 chars, unique per class + Universal) and icon
    (texture name without path, for macros with no #showtooltip spell)."""
    return {"name": name, "code": code, "note": note, "short": short, "icon": icon}

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
          "Only grabs a new enemy if you have no live hostile target.",
          short="SmartTarget", icon="Ability_Hunter_SniperShot"),
        M("Grab TT (take the mob off your friend)",
          "/target [@targettarget, harm, exists]",
          short="GrabTT", icon="Ability_Hunter_MasterMarksman"),
        M("Assist mouseover / friendly target",
          "/assist [@mouseover, help, exists][help]",
          short="Assist@", icon="Ability_Warrior_Challange"),
        M("Clear dead target",
          "/cleartarget [dead]",
          short="ClearDead", icon="Spell_Shadow_SoulLeech_3"),
        M("Skull mark mouseover / target",
          "/targetmarker [@mouseover, exists][] 8",
          "8 = skull, 7 = cross, 5 = moon, 6 = square. Uses the full /targetmarker "
          "name, not the /tm shorthand — the ThreatMaster addon claims /tm for "
          "itself, which silently breaks this macro if you use the short form.",
          short="SkullMark", icon="Ability_MarkOfSkull"),
    ]),

    G(FOCUS, [
        M("Set focus (mouseover first)", "/focus [@mouseover, exists][]",
          short="SetFocus", icon="Ability_Hunter_SniperShot"),
        M("Clear focus", "/clearfocus",
          short="ClearFocus", icon="Spell_Shadow_SoulLeech_3"),
        M("Target focus", "/target focus",
          short="TargetFoc", icon="Ability_Hunter_MasterMarksman"),
        M("Assist focus (set tank as focus)", "/assist focus",
          short="AssistFoc", icon="Ability_Warrior_Challange"),
    ]),

    G(PANIC, [
        M("Healing potion",
          "/use Major Healing Potion",
          "Swap the item name to the potion rank you carry.",
          short="HPotion", icon="INV_Potion_54"),
        M("Mana potion",
          "/use Major Mana Potion",
          "Swap the item name to the potion rank you carry.",
          short="MPotion", icon="INV_Potion_24"),
    ]),

    G(MISC, [
        M("Zoom out more",
          "/console cameraDistanceMaxZoomFactor 4",
          "Raises the max camera zoom-out distance beyond the default cap.",
          short="Zoom", icon="INV_Misc_Spyglass_03"),
        M("Hide guild names",
          "/console UnitNamePlayerGuild 0",
          "Removes guild tags from nameplates and unit frames.",
          short="HideGuild", icon="INV_Misc_GroupLooking"),
        M("Hide PvP titles",
          "/console UnitNamePlayerPVPTitle 0",
          "Removes PvP rank titles from nameplates and unit frames.",
          short="HidePvP", icon="INV_BannerPVP_02"),
        M("Weapon swap: 1H+offhand ↔ 2H",
          "/equipslot 16 Durgen's Crescent Axe\n"
          "/equipslot 17 Veteran Shield\n"
          "/equipslot 16 Ironforge Greathammer",
          "Swap the item names for your own gear. Toggles between 1H+offhand "
          "and 2H each press — slot 16 = main hand, 17 = off hand/shield.",
          short="WeaponSwap", icon="INV_Sword_27"),
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
                M("Shadow Word: Pain", dps("Shadow Word: Pain"), short="SWP"),
                M("Mind Blast", dps("Mind Blast"), short="MBlast"),
                M("Smite", dps("Smite"), short="Smite"),
                M("Holy Fire", dps("Holy Fire"), short="HFire"),
                M("Mana Burn", dps("Mana Burn"), short="ManaBurn"),
            ]),
            G(AUTO, [
                M("Wand (spam-safe)", WAND, short="Wand"),
            ]),
            G(HEAL, [
                M("Flash Heal", heal("Flash Heal"), short="FHeal"),
                M("Heal", heal("Heal"), short="Heal"),
                M("Greater Heal", heal("Greater Heal"), short="GHeal"),
                M("Lesser Heal", heal("Lesser Heal"), short="LHeal"),
                M("Renew", heal("Renew"), short="Renew"),
                M("Power Word: Shield", heal("Power Word: Shield"), short="PWS"),
                M("Prayer of Healing", plain("Prayer of Healing"), "Party-wide, no target needed.", short="PoH"),
                M("Resurrection", heal("Resurrection"), short="Rez"),
            ]),
            G(CLEAN, [
                M("Dispel Magic (friend or foe)", util("Dispel Magic"), short="Dispel"),
                M("Cure Disease", heal("Cure Disease"), short="CureDisease"),
                M("Abolish Disease", heal("Abolish Disease"), short="AbolishDis"),
            ]),
            G(BUFF, [
                M("Power Word: Fortitude", buff("Power Word: Fortitude"), short="PWFort"),
                M("Prayer of Fortitude", buff("Prayer of Fortitude"), short="PoFort"),
                M("Shadow Protection", buff("Shadow Protection"), short="ShadowProt"),
                M("Levitate", buff("Levitate"), short="Levitate"),
                M("Inner Fire", plain("Inner Fire"), short="InnerFire"),
                M("Fear Ward", buff("Fear Ward"), "Racial/availability may differ in Forever.", short="FearWard"),
            ]),
            G(PANIC, [
                M("Shield self", me("Power Word: Shield"), short="PWS me"),
                M("Psychic Scream", plain("Psychic Scream"), short="Scream"),
                M("Fade", plain("Fade"), short="Fade"),
                M("Desperate Prayer", plain("Desperate Prayer"), "Racial priest spell.", short="DesperatePr"),
            ]),
            G(FOCUS, [
                M("Shackle Undead on focus", foc("Shackle Undead"), short="Shackle F"),
                M("Mind Control on focus", foc("Mind Control"), short="MindCtrl F"),
            ]),
        ]},

        {"spec": "Shadow", "groups": [
            G(DPS, [
                M("Mind Flay (spam-safe)", chan("Mind Flay"), "Won't clip an active channel.", short="MFlay"),
                M("Vampiric Embrace", dps("Vampiric Embrace"), short="VampEmb"),
                M("Silence (interrupt)", "#showtooltip Silence\n/stopcasting\n/cast [@targettarget, harm, exists][harm] Silence",
                  "Clears your current cast first so the interrupt fires instantly.", short="Silence"),
                M("Devouring Plague", dps("Devouring Plague"), "Racial priest spell.", short="DevPlague"),
            ]),
            G(BUFF, [
                M("Shadowform (no cancel)",
                  "#showtooltip Shadowform\n/cast [noform] Shadowform",
                  "Won't drop you out of form if pressed again.", short="Shadowform"),
            ]),
            G(FOCUS, [
                M("Silence focus", "#showtooltip Silence\n/stopcasting\n/cast [@focus, harm, exists][harm] Silence",
                  "Clears your current cast first so the interrupt fires instantly.", short="Silence F"),
            ]),
        ]},

        {"spec": "Holy", "groups": [
            G(HEAL, [
                M("Inner Focus + Greater Heal",
                  "#showtooltip Greater Heal\n/cast Inner Focus\n/cast [@mouseover, help, exists][help][@player] Greater Heal",
                  short="IF+GHeal"),
                M("Holy Nova", plain("Holy Nova"), short="HNova"),
                M("Prayer of Mending", heal("Prayer of Mending"),
                  "New in Forever. Heals, then jumps to another group member when they take damage.", short="PoM"),
                M("Lightwell", plain("Lightwell"), short="Lightwell"),
            ]),
        ]},

        {"spec": "Discipline", "groups": [
            G(HEAL, [
                M("Power Infusion", heal("Power Infusion"), short="PowerInf"),
                M("Penance (friend or foe)", util("Penance"),
                  "New in Forever. Heals a friendly mouseover/target, damages an enemy one.", short="Penance"),
                M("Inner Focus + Greater Heal",
                  "#showtooltip Greater Heal\n/cast Inner Focus\n/cast [@mouseover, help, exists][help][@player] Greater Heal",
                  short="InnerFocus"),
            ]),
            G(BUFF, [
                M("Divine Spirit", buff("Divine Spirit"), short="DivSpirit"),
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
                  "pulling or burning mana. With any other demon the Firebolt line is skipped.",
                  short="ShadowBolt"),
                M("Corruption", dpsHarm("Corruption"), short="Corrupt"),
                M("Curse of Agony", dpsHarm("Curse of Agony"), short="CoAgony"),
                M("Immolate", dpsHarm("Immolate"), short="Immolate"),
                M("Searing Pain", dpsHarm("Searing Pain"), short="Searing"),
                M("Soul Fire", dpsHarm("Soul Fire"), short="SoulFire"),
                M("Death Coil", dpsHarm("Death Coil"), short="DeathCoil"),
                M("Drain Life (spam-safe)", chan("Drain Life"), short="DrainLife"),
                M("Drain Soul (spam-safe)", chan("Drain Soul"), short="DrainSoul"),
                M("Drain Mana (spam-safe)", chan("Drain Mana"), short="DrainMana"),
                M("Curse of the Elements", dpsHarm("Curse of the Elements"), short="CoElements"),
                M("Curse of Shadow", dpsHarm("Curse of Shadow"), short="CoShadow"),
                M("Curse of Recklessness", dpsHarm("Curse of Recklessness"), short="CoReck"),
                M("Curse of Weakness", dpsHarm("Curse of Weakness"), short="CoWeak"),
                M("Curse of Tongues", dpsHarm("Curse of Tongues"), short="CoTongues"),
                M("Hellfire", plain("Hellfire"), short="Hellfire"),
                M("Rain of Fire", plain("Rain of Fire"), short="RoF"),
            ]),
            G(AUTO, [
                M("Wand (spam-safe)", WAND, short="Wand"),
            ]),
            G(HEAL, [
                M("Health Funnel (pet)", plain("Health Funnel"), short="HFunnel"),
                M("Unending Breath", buff("Unending Breath"), short="UnendBreath"),
                M("Detect Invisibility", buff("Detect Invisibility"), short="DetectInv"),
                M("Soulstone mouseover",
                  "/use [@mouseover, help, exists][help] Major Soulstone",
                  "Swap item name to your soulstone rank.", short="Soulstone", icon="INV_Misc_Orb_04"),
            ]),
            G(CLEAN, [
                M("Devour Magic (Felhunter)", heal("Devour Magic"), short="DevourMagic"),
            ]),
            G(BUFF, [
                M("Demon Armor", plain("Demon Armor"), short="DemonArmor"),
                M("Shadow Ward", plain("Shadow Ward"), short="ShadowWard"),
            ]),
            G(PANIC, [
                M("Healthstone", "/use Major Healthstone", "Swap item name to your healthstone rank.",
                  short="Healthstone", icon="INV_Stone_04"),
                M("Howl of Terror", plain("Howl of Terror"), short="HowlTerror"),
                M("Fear", dpsHarm("Fear"), short="Fear"),
                M("Sacrifice (Voidwalker)", plain("Sacrifice"), short="Sacrifice"),
                M("Life Tap", plain("Life Tap"), short="LifeTap"),
            ]),
            G(QOL, [
                M("Pet attack TT / target", PETATK, short="PetAtk", icon="Ability_GhoulFrenzy"),
                M("Pet follow", "/petfollow", short="PetFollow", icon="Ability_Hunter_BeastCall"),
                M("Pet passive", "/petpassive", short="PetPassive", icon="Ability_Hunter_BeastSoothe"),
                M("Pet defensive", "/petdefensive", short="PetDef", icon="Ability_Druid_Cower"),
                M("Spell Lock (Felhunter)", dpsHarm("Spell Lock"), short="SpellLock"),
                M("Torment (Voidwalker taunt)", dpsHarm("Torment"), short="Torment"),
                M("Summon Felhunter", plain("Summon Felhunter"), short="SummonFH"),
                M("Summon Voidwalker", plain("Summon Voidwalker"), short="SummonVW"),
                M("Summon Succubus", plain("Summon Succubus"), short="SummonSucc"),
                M("Summon Imp", plain("Summon Imp"), short="SummonImp"),
            ]),
            G(FOCUS, [
                M("Fear focus", foc("Fear"), short="Fear F"),
                M("Banish focus", foc("Banish"), short="Banish F"),
                M("Seduction focus", foc("Seduction"), short="Seduce F"),
                M("Spell Lock focus", foc("Spell Lock"), short="SpellLock F"),
                M("Enslave Demon focus", foc("Enslave Demon"), short="Enslave F"),
                M("Bane of Havoc focus", foc("Bane of Havoc"),
                  "New in Forever. Put it on a second mob (focus), then nuke your target: "
                  "part of your damage is copied onto the focus.", short="BoHavoc F"),
            ]),
        ]},

        {"spec": "Affliction", "groups": [
            G(DPS, [
                M("Siphon Life", dpsHarm("Siphon Life"), short="SiphonLife"),
                M("Curse of Exhaustion", dpsHarm("Curse of Exhaustion"), short="CoExhaust"),
                M("Wrack (spam-safe)", chan("Wrack"),
                  "New in Forever. Channeled drain that makes the target take more Shadow DoT damage.", short="Wrack"),
                M("Amplify Curse + Agony",
                  "#showtooltip Curse of Agony\n/cast Amplify Curse\n/cast [harm] Curse of Agony", short="AmpCurse"),
                M("DoT sequence (press to roll dots)",
                  "#showtooltip Corruption\n"
                  "/castsequence [harm] reset=target Corruption, Curse of Agony, Siphon Life, Immolate",
                  short="DoTSeq"),
            ]),
            G(PANIC, [
                M("Dark Pact", plain("Dark Pact"),
                  BETA + "not seen in the Forever beta talent tree, may be removed.", short="DarkPact"),
            ]),
        ]},

        {"spec": "Demonology", "groups": [
            G(QOL, [
                M("Fel Domination + Felhunter",
                  "#showtooltip Summon Felhunter\n/cast Fel Domination\n/cast Summon Felhunter", short="FelDom+FH"),
                M("Fel Domination + Voidwalker",
                  "#showtooltip Summon Voidwalker\n/cast Fel Domination\n/cast Summon Voidwalker", short="FelDom+VW"),
                M("Soul Link", plain("Soul Link"), short="SoulLink"),
                M("Demonic Sacrifice", plain("Demonic Sacrifice"), short="DemonicSac"),
            ]),
        ]},

        {"spec": "Destruction", "groups": [
            G(DPS, [
                M("Conflagrate", dpsHarm("Conflagrate"), short="Conflag"),
                M("Shadowburn", dpsHarm("Shadowburn"), short="Shadowburn"),
                M("Incinerate", dpsHarm("Incinerate"),
                  "New in Forever. Hits harder when Immolate is on the target.", short="Incinerate"),
                M("Immolate > Conflagrate",
                  "#showtooltip Immolate\n"
                  "/castsequence [harm] reset=target/10 Immolate, Conflagrate", short="Immo>Conflag"),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # MAGE
    # -------------------------------------------------------------------- #
    {"name": "Mage", "color": "#69CCF0", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Frostbolt", dpsHarm("Frostbolt"), short="Frostbolt"),
                M("Fireball", dpsHarm("Fireball"), short="Fireball"),
                M("Arcane Missiles (spam-safe)", chan("Arcane Missiles"), short="ArcMissiles"),
                M("Arcane Explosion", plain("Arcane Explosion"), short="ArcExplosion"),
                M("Fire Blast", dpsHarm("Fire Blast"), short="FireBlast"),
                M("Frost Nova", "#showtooltip Frost Nova\n/stopcasting\n/cast [harm] Frost Nova",
                  "Clears your current cast first so the root fires instantly.", short="FrostNova"),
                M("Cone of Cold", plain("Cone of Cold"), short="ConeOfCold"),
                M("Scorch", dpsHarm("Scorch"), short="Scorch"),
                M("Counterspell (interrupt)", "#showtooltip Counterspell\n/stopcasting\n/cast [harm] Counterspell",
                  "Clears your current cast first so the interrupt fires instantly.", short="CSpell"),
                M("Polymorph", dpsHarm("Polymorph"), short="Polymorph"),
                M("Polymorph + Diamond mark",
                  "#showtooltip Polymorph\n/targetmarker [harm] 3\n/cast [harm] Polymorph",
                  "Marks the sheep target with a diamond so the group knows not to break it. "
                  "Uses the full /targetmarker name, not /tm — the ThreatMaster addon claims "
                  "/tm for itself, which silently breaks this macro if you use the short form.",
                  short="Poly+Mark"),
            ]),
            G(HEAL, [
                M("Mana Shield", plain("Mana Shield"), short="ManaShield"),
            ]),
            G(BUFF, [
                M("Arcane Intellect", buff("Arcane Intellect"), short="ArcInt"),
                M("Frost Armor", plain("Frost Armor"), short="FrostArmor"),
                M("Ice Armor", plain("Ice Armor"), short="IceArmor"),
                M("Molten Armor", plain("Molten Armor"), short="MoltenArmor"),
                M("Dampen Magic", buff("Dampen Magic"), short="DampenMagic"),
                M("Amplify Magic", buff("Amplify Magic"), short="AmpMagic"),
            ]),
            G(PANIC, [
                M("Ice Block (press again to cancel)",
                  "#showtooltip Ice Block\n/cancelaura Ice Block\n/cast Ice Block",
                  "First press casts Ice Block, second press cancels it early.", short="IceBlock"),
                M("Blink", plain("Blink"), short="Blink"),
                M("Evocation", plain("Evocation"), short="Evocation"),
            ]),
            G(QOL, [
                M("Conjure Food", plain("Conjure Food"), short="ConjFood"),
                M("Conjure Water", plain("Conjure Water"), short="ConjWater"),
                M("Summon Water Elemental", plain("Summon Water Elemental"), short="SummonWE"),
                M("Remove Curse", heal("Remove Curse"), short="RemoveCurse"),
            ]),
            G(CLEAN, [
                M("Remove Curse (friend or foe)", util("Remove Curse"), short="RemCurse@"),
            ]),
            G(FOCUS, [
                M("Counterspell focus", "#showtooltip Counterspell\n/stopcasting\n/cast [@focus, harm, exists][harm] Counterspell",
                  "Clears your current cast first so the interrupt fires instantly.", short="CSpell F"),
                M("Polymorph focus", foc("Polymorph"), short="Poly F"),
            ]),
        ]},

        {"spec": "Arcane", "groups": [
            G(DPS, [
                M("Arcane Power + Arcane Missiles", "#showtooltip Arcane Missiles\n/cast Arcane Power\n/cast [harm] Arcane Missiles",
                  short="APower+AMiss"),
                M("Presence of Mind + Frostbolt", "#showtooltip Frostbolt\n/cast Presence of Mind\n/cast [harm] Frostbolt", "Instant-cast next spell.",
                  short="PoM+Frost"),
                M("Presence of Mind + Pyroblast", "#showtooltip Pyroblast\n/cast Presence of Mind\n/cast [harm] Pyroblast",
                  "The classic burst combo for Arcane/Fire hybrids: instant Pyroblast.", short="PoM+Pyro"),
                M("Arcane Blast", dpsHarm("Arcane Blast"),
                  "New in Forever. Each cast in a row costs more and powers up your next other spell.", short="ArcBlast"),
            ]),
        ]},

        {"spec": "Fire", "groups": [
            G(DPS, [
                M("Combustion", plain("Combustion"), short="Combustion"),
                M("Pyroblast", dpsHarm("Pyroblast"), short="Pyroblast"),
            ]),
        ]},

        {"spec": "Frost", "groups": [
            G(DPS, [
                M("Ice Lance", dpsHarm("Ice Lance"), short="IceLance"),
                M("Cold Snap", plain("Cold Snap"), short="ColdSnap"),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # ROGUE
    # -------------------------------------------------------------------- #
    {"name": "Rogue", "color": "#FFF569", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Sinister Strike", melee("Sinister Strike"), short="SinStrike"),
                M("Backstab", melee("Backstab"), short="Backstab"),
                M("Eviscerate", melee("Eviscerate"), short="Evisc"),
                M("Gouge", dpsHarm("Gouge"), short="Gouge"),
                M("Gouge (mouseover)", "#showtooltip Gouge\n/cast [@mouseover, harm, nodead][harm, nodead] Gouge",
                  short="Gouge@"),
                M("Kidney Shot", melee("Kidney Shot"), short="KidneyShot"),
                M("Rupture", melee("Rupture"), short="Rupture"),
                M("Garrote", melee("Garrote"), "Requires stealth.", short="Garrote"),
                M("Ambush", melee("Ambush"), "Requires stealth.", short="Ambush"),
                M("Cheap Shot", melee("Cheap Shot"), "Requires stealth. Classic stunlock opener.", short="CheapShot"),
                M("Expose Armor", dpsHarm("Expose Armor"), short="ExposeArmor"),
                M("Sap", dpsHarm("Sap"), "Only works on an out-of-combat target.", short="Sap"),
                M("Kick (interrupt)", "#showtooltip Kick\n/stopcasting\n/cast [harm] Kick",
                  "Clears your current cast first so the interrupt fires instantly.", short="Kick"),
                M("Kick (mouseover)", "#showtooltip Kick\n/stopcasting\n/cast [@mouseover, harm, nodead][harm, nodead] Kick",
                  "Clears your current cast first so the interrupt fires instantly.", short="Kick@"),
            ]),
            G(AUTO, [
                M("Auto-attack (spam-safe)", MELEE, short="Attack", icon="Ability_GhoulFrenzy"),
                M("Ranged weapon (Bow/Gun/Crossbow/Thrown)",
                  "#showtooltip\n/cast [equipped:Bows] Shoot Bow; [equipped:Guns] Shoot Gun; "
                  "[equipped:Crossbows] Shoot Crossbow; [equipped:Thrown] Throw",
                  "One button for whatever ranged weapon you have equipped.", short="Ranged"),
            ]),
            G(BUFF, [
                M("Slice and Dice", plain("Slice and Dice"), short="SnD"),
            ]),
            G(PANIC, [
                M("Evasion", plain("Evasion"), short="Evasion"),
                M("Vanish", plain("Vanish"), short="Vanish"),
                M("Sprint", plain("Sprint"), short="Sprint"),
                M("Blind", dpsHarm("Blind"), short="Blind"),
                M("Blind (mouseover)", "#showtooltip Blind\n/cast [@mouseover, harm, nodead][harm, nodead] Blind",
                  short="Blind@"),
            ]),
            G(QOL, [
                M("Stealth (no cancel)", "#showtooltip Stealth\n/cast [nostealth] Stealth", "Won't drop you out of stealth if pressed again.",
                  short="Stealth"),
                M("Pick Lock", plain("Pick Lock"), short="PickLock"),
                M("Pick Pocket", dpsHarm("Pick Pocket"), short="PickPocket"),
                M("Pick Pocket (mouseover)", "#showtooltip Pick Pocket\n/cast [@mouseover, harm, nodead][harm, nodead] Pick Pocket",
                  short="PickPkt@"),
                M("Pick Pocket + Sap",
                  "#showtooltip Sap\n/cast [harm] Pick Pocket\n/cast [harm] Sap",
                  "Pick Pocket has no global cooldown, so one press robs and saps.", short="PickPkt+Sap"),
                M("Apply poison (left = main, right = off hand)",
                  "#showtooltip Instant Poison\n/use Instant Poison\n/use [button:1] 16; [button:2] 17\n/click StaticPopup1Button1",
                  "Change the poison name to the rank you have (e.g. Instant Poison II). The last line "
                  "confirms the \"replace enchant\" popup.", short="Poison", icon="INV_Potion_02"),
                M("Distract", "#showtooltip Distract\n/cast [@cursor] Distract", short="Distract"),
                M("Feint", dpsHarm("Feint"), short="Feint"),
                M("Grenade at cursor", "#showtooltip Iron Grenade\n/use [@cursor] Iron Grenade",
                  "Swap the item name for the grenade you carry.", short="Grenade", icon="INV_Misc_Bomb_08"),
                M("Sharpening stone (left = main, right = off hand)",
                  "#showtooltip Rough Sharpening Stone\n/use Rough Sharpening Stone\n/use [button:1] 16; [button:2] 17\n"
                  "/click StaticPopup1Button1",
                  "Swap the item name for the stone you carry. The last line confirms the \"replace enchant\" popup.",
                  short="Stone", icon="INV_Stone_02"),
            ]),
            G(CLEAN, [
                M("No dispel", "", "Rogues have no dispel. Interrupt instead with Kick, or silence with Gouge/Kidney Shot/Blind."),
            ]),
            G(FOCUS, [
                M("Kick focus", "#showtooltip Kick\n/stopcasting\n/cast [@focus, harm, exists][harm] Kick",
                  "Clears your current cast first so the interrupt fires instantly.", short="Kick F"),
                M("Kidney Shot focus", foc("Kidney Shot"), short="KidneyShot F"),
                M("Blind focus", foc("Blind"), short="Blind F"),
            ]),
        ]},

        {"spec": "Assassination", "groups": [
            G(DPS, [
                M("Venom", dpsHarm("Venom"),
                  "Forever's finisher (replaces Envenom): boosts poison damage and proc chance. "
                  "Longer duration per combo point.", short="Venom"),
                M("Mutilate", melee("Mutilate"), short="Mutilate"),
                M("Cold Blood + Ambush", "#showtooltip Ambush\n/cast Cold Blood\n/cast [harm] Ambush", "Requires stealth.",
                  short="ColdBlood+Amb"),
            ]),
        ]},

        {"spec": "Combat", "groups": [
            G(DPS, [
                M("Blade Flurry", plain("Blade Flurry"), short="BladeFlurry"),
                M("Adrenaline Rush", plain("Adrenaline Rush"), short="AdrenRush"),
            ]),
        ]},

        {"spec": "Subtlety", "groups": [
            G(DPS, [
                M("Hemorrhage", melee("Hemorrhage"), short="Hemo"),
                M("Premeditation", plain("Premeditation"), "Requires stealth.", short="Premed"),
            ]),
            G(PANIC, [
                M("Cloak of Shadows", plain("Cloak of Shadows"), short="CloakShadow"),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # SHAMAN
    # -------------------------------------------------------------------- #
    {"name": "Shaman", "color": "#0070DE", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Lightning Bolt", dpsHarm("Lightning Bolt"), short="LBolt"),
                M("Chain Lightning", dpsHarm("Chain Lightning"), short="CLightning"),
                M("Earth Shock (interrupt)", "#showtooltip Earth Shock\n/stopcasting\n/cast [harm] Earth Shock",
                  "Clears your current cast first so the interrupt fires instantly.", short="EShock"),
                M("Flame Shock", dpsHarm("Flame Shock"), short="FlameShock"),
                M("Frost Shock", dpsHarm("Frost Shock"), short="FrostShock"),
                M("Purge (offensive dispel)", dpsHarm("Purge"), short="Purge"),
            ]),
            G(AUTO, [
                M("Auto-attack (spam-safe)", MELEE, short="Attack", icon="Ability_GhoulFrenzy"),
            ]),
            G(HEAL, [
                M("Healing Wave", heal("Healing Wave"), short="HWave"),
                M("Lesser Healing Wave", heal("Lesser Healing Wave"), short="LHWave"),
                M("Chain Heal", heal("Chain Heal"), short="ChainHeal"),
                M("Ancestral Spirit", heal("Ancestral Spirit"), short="AncSpirit"),
                M("Riptide", heal("Riptide"),
                  "New in Forever. Instant heal + HoT that boosts your next Chain Heal.", short="Riptide"),
            ]),
            G(CLEAN, [
                M("Cure Poison", heal("Cure Poison"), short="CurePoison"),
                M("Cure Disease", heal("Cure Disease"), short="CureDisease"),
            ]),
            G(BUFF, [
                M("Lightning Shield", plain("Lightning Shield"), short="LShield"),
                M("Water Shield", plain("Water Shield"),
                  "New in Forever. Mana back when you're hit or crit-heal. Replaces Lightning Shield for healers.",
                  short="WShield"),
                M("Rockbiter Weapon", plain("Rockbiter Weapon"), short="Rockbiter"),
                M("Flametongue Weapon", plain("Flametongue Weapon"), short="Flametongue"),
                M("Frostbrand Weapon", plain("Frostbrand Weapon"), short="Frostbrand"),
                M("Water Walking", buff("Water Walking"), short="WaterWalk"),
                M("Water Breathing", buff("Water Breathing"), short="WaterBreath"),
            ]),
            G(PANIC, [
                M("Self Lesser Healing Wave", me("Lesser Healing Wave"), short="SelfLHWave"),
                M("Stoneclaw Totem", plain("Stoneclaw Totem"), short="Stoneclaw"),
                M("Grounding Totem", plain("Grounding Totem"), short="Grounding"),
                M("Ghost Wolf (no cancel)", "#showtooltip Ghost Wolf\n/cast [noform] Ghost Wolf", short="GhostWolf"),
            ]),
            G(QOL, [
                M("Totems: melee group (press 4x)",
                  "#showtooltip Strength of Earth Totem\n"
                  "/castsequence reset=combat Strength of Earth Totem, Windfury Totem, Searing Totem, Mana Spring Totem",
                  short="MeleeTotems"),
                M("Totems: caster group (press 4x)",
                  "#showtooltip Stoneskin Totem\n"
                  "/castsequence reset=combat Stoneskin Totem, Grace of Air Totem, Searing Totem, Mana Spring Totem",
                  "Swap Grace of Air for Tranquil Air if you prefer.", short="CasterTotems"),
                M("Tremor Totem", plain("Tremor Totem"), short="Tremor"),
                M("Poison Cleansing Totem", plain("Poison Cleansing Totem"), short="PoisonCleanse"),
                M("Disease Cleansing Totem", plain("Disease Cleansing Totem"), short="DiseaseCleanse"),
                M("Earthbind Totem", plain("Earthbind Totem"), short="Earthbind"),
                M("Magma Totem", plain("Magma Totem"), short="Magma"),
                M("Fire Nova Totem", plain("Fire Nova Totem"), short="FireNova"),
                M("Healing Stream Totem", plain("Healing Stream Totem"), short="HealStream"),
            ]),
            G(FOCUS, [
                M("Earth Shock interrupt on focus", "#showtooltip Earth Shock\n/stopcasting\n/cast [@focus, harm, exists][harm] Earth Shock",
                  "Clears your current cast first so the interrupt fires instantly.", short="EShock F"),
                M("Purge focus", foc("Purge"), short="Purge F"),
            ]),
        ]},

        {"spec": "Elemental", "groups": [
            G(DPS, [
                M("Lava Burst", dpsHarm("Lava Burst"),
                  "New in Forever. Hits 20% harder with your Flame Shock on the target.", short="LavaBurst"),
                M("Flame Shock > Lava Burst",
                  "#showtooltip Flame Shock\n/castsequence [harm] reset=target/12 Flame Shock, Lava Burst",
                  "Opener: Flame Shock, then the boosted Lava Burst.", short="Flame>Lava"),
                M("Elemental Mastery + Chain Lightning",
                  "#showtooltip Chain Lightning\n/cast Elemental Mastery\n/cast [harm] Chain Lightning",
                  BETA + "Elemental Mastery was not seen in the Forever beta talent tree.", short="EleMastery+CL"),
                M("Elemental Mastery + Lightning Bolt",
                  "#showtooltip Lightning Bolt\n/cast Elemental Mastery\n/cast [harm] Lightning Bolt",
                  BETA + "Elemental Mastery was not seen in the Forever beta talent tree.", short="EleMastery+LB"),
            ]),
        ]},

        {"spec": "Enhancement", "groups": [
            G(DPS, [
                M("Stormstrike", dpsHarm("Stormstrike"),
                  "Also starts auto-attack. In Forever it boosts only your NEXT Lightning Bolt, "
                  "Chain Lightning or Earth Shock, so follow up with one.", short="Stormstrike"),
            ]),
            G(BUFF, [
                M("Windfury Weapon", plain("Windfury Weapon"), short="Windfury"),
                M("Windfury Weapon + Lightning Shield refresh",
                  "#showtooltip Lightning Shield\n/castsequence reset=2 Lightning Shield, Windfury Weapon",
                  "Press twice to reapply both buffs; resets after 2 sec so it doesn't get stuck mid-sequence.",
                  short="WF+LSRefresh"),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # HUNTER
    # -------------------------------------------------------------------- #
    {"name": "Hunter", "color": "#ABD473", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Hunter's Mark", dpsHarm("Hunter's Mark"), short="HMark"),
                M("Hunter's Mark + send pet (opener)",
                  "#showtooltip Hunter's Mark\n/petattack [harm]\n/cast [harm] Hunter's Mark",
                  "One press marks the target and sends the pet in.", short="HMark+Pet"),
                M("Serpent Sting", dpsHarm("Serpent Sting"), short="SerpentSting"),
                M("Arcane Shot", dpsHarm("Arcane Shot"), short="ArcaneShot"),
                M("Multi-Shot", dpsHarm("Multi-Shot"),
                  "Forever: 0.5 sec cast, 6 sec cooldown. Stand still for it.", short="MultiShot"),
                M("Volley at cursor", "#showtooltip Volley\n/cast [@cursor] Volley",
                  "Forever removed Volley's cooldown, so it's a real AoE button now. "
                  "Drops at your mouse cursor, no targeting circle.", short="Volley"),
                M("Concussive Shot", dpsHarm("Concussive Shot"), short="ConcShot"),
                M("Viper Sting", dpsHarm("Viper Sting"), short="ViperSting"),
                M("Scorpid Sting", dpsHarm("Scorpid Sting"), short="ScorpidSting"),
                M("Raptor Strike + Wing Clip",
                  "#showtooltip Raptor Strike\n/cast [harm] Raptor Strike\n/cast [harm] Wing Clip", short="Raptor+Clip"),
                M("Mongoose Bite", dpsHarm("Mongoose Bite"), short="Mongoose"),
                M("Raptor Strike + Mongoose Bite + Wing Clip (test — GCD may skip some)",
                  "#showtooltip Raptor Strike\n/cast [harm] Raptor Strike\n/cast [harm] Mongoose Bite\n/cast [harm] Wing Clip",
                  "Experimental 3-in-1. Only the first ability that both fires and consumes the GCD will actually go off per press — likely to just spam Raptor Strike. Testing to see how WoW Forever's client handles the fallthrough.",
                  short="Raptor3in1"),
                M("Wing Clip", dpsHarm("Wing Clip"), short="WingClip"),
                M("Distracting Shot", dpsHarm("Distracting Shot"), short="DistractShot"),
                M("Tranquilizing Shot (enrage dispel)",
                  dpsHarm("Tranquilizing Shot"),
                  "Hunter's only dispel: removes Frenzy from enemies.", short="TranqShot"),
            ]),
            G(AUTO, [
                M("Auto Shot (spam-safe)",
                  "#showtooltip Auto Shot\n/cast [@targettarget, harm, exists][harm] !Auto Shot",
                  "Hunter exception: ! stops Auto Shot toggling off. Unlike wand Shoot, it works here.",
                  short="AutoShot"),
                M("Melee auto-attack", MELEE, short="Attack", icon="Ability_GhoulFrenzy"),
            ]),
            G(BUFF, [
                M("Aspect: Hawk in combat, Cheetah out",
                  "#showtooltip Aspect of the Hawk\n/cast [combat] Aspect of the Hawk; Aspect of the Cheetah",
                  short="AspectHawk"),
                M("Aspect toggle: Cheetah ↔ Hawk",
                  "#showtooltip\n/castsequence reset=combat Aspect of the Cheetah, Aspect of the Hawk",
                  "Each press swaps to the other aspect; the icon shows the next one. "
                  "Resets after combat, so the first press after a fight is always Cheetah. "
                  "Cheetah dazes you when hit, so press again before pulling.", short="AspectToggle"),
                M("Aspect of the Hawk", plain("Aspect of the Hawk"), short="AspHawk"),
                M("Aspect of the Monkey", plain("Aspect of the Monkey"), short="AspMonkey"),
                M("Aspect of the Pack", plain("Aspect of the Pack"), short="AspPack"),
                M("Aspect of the Wild", plain("Aspect of the Wild"), short="AspWild"),
            ]),
            G(PANIC, [
                M("Feign Death (clean)",
                  "#showtooltip Feign Death\n/petfollow\n/stopattack\n/cast Feign Death",
                  "Calls the pet back and stops attacking first, so the pet doesn't keep mobs on you.", short="FeignDeath"),
                M("Disengage", dpsHarm("Disengage"), short="Disengage"),
                M("Freezing Trap", plain("Freezing Trap"), short="FreezeTrap"),
                M("Frost Trap", plain("Frost Trap"), short="FrostTrap"),
                M("Rapid Fire", plain("Rapid Fire"), short="RapidFire"),
            ]),
            G(QOL, [
                M("Pet attack TT / target", PETATK, short="PetAtk", icon="Ability_GhoulFrenzy"),
                M("Pet attack mouseover", PETATK_MO,
                  "Attacks the enemy under your mouse, else your target. " + PET_ICON_NOTE,
                  short="PetAtkMO", icon="Ability_GhoulFrenzy"),
                M("Pet attack mouseover / TT", PETATK_MO_TT,
                  "Mouseover first, then your target's target, then your target. " + PET_ICON_NOTE,
                  short="PetAtkMOTT", icon="Ability_GhoulFrenzy"),
                M("Pet attack / Shift = follow", PETATK_SHIFT,
                  "Press to send the pet (mouseover first); Shift+press calls it back. " + PET_ICON_NOTE,
                  short="PetAtkShift", icon="Ability_GhoulFrenzy"),
                M("Pet follow", "/petfollow", short="PetFollow", icon="Ability_Hunter_BeastCall"),
                M("Pet passive", "/petpassive", short="PetPassive", icon="Ability_Hunter_BeastSoothe"),
                M("Call / Revive / Mend (one button)",
                  "#showtooltip Mend Pet\n/cast [nopet] Call Pet; [@pet, dead] Revive Pet; Mend Pet", short="PetMend"),
                M("Feed Pet",
                  "#showtooltip Feed Pet\n/cast Feed Pet\n/use Tough Jerky",
                  "Swap food item for your pet's diet.", short="FeedPet"),
                M("Flare", plain("Flare"), short="Flare"),
                M("Explosive Trap", plain("Explosive Trap"), short="ExploTrap"),
                M("Immolation Trap", plain("Immolation Trap"), short="ImmoTrap"),
            ]),
            G(CLEAN, [
                M("No friendly dispel", "",
                  "Hunters have no friendly cleanse. Use Tranquilizing Shot (Damage / offensive) instead."),
            ]),
            G(FOCUS, [
                M("Hunter's Mark focus", foc("Hunter's Mark"), short="HMark F"),
                M("Concussive Shot focus", foc("Concussive Shot"), short="ConcShot F"),
            ]),
        ]},

        {"spec": "Beast Mastery", "groups": [
            G(DPS, [
                M("Bestial Wrath + Rapid Fire burst",
                  "#showtooltip Bestial Wrath\n/cast Bestial Wrath\n/cast Rapid Fire", short="BW+RapidFire"),
                M("Intimidation + pet attack",
                  "#showtooltip Intimidation\n/petattack [harm]\n/cast Intimidation",
                  "Intimidation only fires on the pet's next hit, so this sends the pet in too.", short="Intim+Pet"),
            ]),
        ]},

        {"spec": "Marksmanship", "groups": [
            G(DPS, [
                M("Aimed Shot", dpsHarm("Aimed Shot"), short="AimedShot"),
                M("Scatter Shot", dpsHarm("Scatter Shot"), short="ScatterShot"),
            ]),
            G(BUFF, [
                M("Trueshot Aura", plain("Trueshot Aura"), short="TrueshotAura"),
            ]),
            G(FOCUS, [
                M("Scatter Shot focus", foc("Scatter Shot"), short="ScatterShot F"),
            ]),
        ]},

        {"spec": "Survival", "groups": [
            G(DPS, [
                M("Counterattack", dpsHarm("Counterattack"), short="Counterattack"),
                M("Strider Kick", dpsHarm("Strider Kick"),
                  "New Survival talent in Forever: instant 100% weapon damage kick, 8 sec cooldown.", short="StriderKick"),
                M("Survival melee button (Raptor + Mongoose + Strider Kick)",
                  "#showtooltip Raptor Strike\n/startattack [harm]\n/cast [harm] Raptor Strike\n"
                  "/cast [harm] Mongoose Bite\n/cast [harm] Strider Kick",
                  BETA + "Raptor Strike queues on your next swing (no global cooldown), then "
                  "Mongoose Bite if it's lit up, else Strider Kick. Spam it in melee.", short="SurvMelee"),
            ]),
            G(PANIC, [
                M("Deterrence", plain("Deterrence"), short="Deterrence"),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # PALADIN
    # -------------------------------------------------------------------- #
    {"name": "Paladin", "color": "#F58CBA", "sections": [

        {"spec": "General", "groups": [
            G(DPS, [
                M("Holy Strike + auto-attack",
                  "#showtooltip Holy Strike\n/startattack [harm]\n/cast [harm] Holy Strike",
                  "New baseline strike in Forever (level 6, 12 sec cooldown).", short="HStrike"),
                M("Judgement", dpsHarm("Judgement"),
                  "Forever: Judgement no longer uses up your seal, so no reseal needed.", short="Judge"),
                M("Hammer of Wrath", dpsHarm("Hammer of Wrath"), short="HoW"),
                M("Exorcism", dpsHarm("Exorcism"), short="Exo"),
                M("Hammer of Justice", dpsMO("Hammer of Justice"),
                  "Stuns whatever's under your mouse without changing your target; "
                  "falls back to your target if nothing's under the mouse.", short="HoJ"),
                M("Consecration", plain("Consecration"), short="Consec"),
                M("Holy Wrath", plain("Holy Wrath"), short="HWrath"),
            ]),
            G(AUTO, [
                M("Auto-attack (spam-safe)", MELEE, short="Attack", icon="Ability_GhoulFrenzy"),
            ]),
            G(HEAL, [
                M("Holy Light", heal("Holy Light"), short="HL"),
                M("Flash of Light", heal("Flash of Light"), short="FoL"),
                M("Lay on Hands", heal("Lay on Hands"), short="LoH"),
                M("Blessing of Protection", heal("Blessing of Protection"), short="BoP"),
                M("Blessing of Freedom", heal("Blessing of Freedom"), short="BoF"),
                M("Redemption", heal("Redemption"), short="Rez"),
            ]),
            G(CLEAN, [
                M("Cleanse", heal("Cleanse"), short="Cleanse"),
                M("Purify", heal("Purify"), short="Purify"),
            ]),
            G(BUFF, [
                M("Blessing of Might", buff("Blessing of Might"), short="BoM"),
                M("Blessing of Wisdom", buff("Blessing of Wisdom"), short="BoW"),
                M("Blessing of Salvation", buff("Blessing of Salvation"), short="Salv"),
                M("Blessing of Light", buff("Blessing of Light"), short="BoL"),
                M("Greater Blessing of Might", buff("Greater Blessing of Might"), short="GBoM"),
                M("Greater Blessing of Wisdom", buff("Greater Blessing of Wisdom"), short="GBoW"),
                M("Devotion Aura", plain("Devotion Aura"), short="Devo"),
                M("Retribution Aura", plain("Retribution Aura"), short="RetAura"),
                M("Concentration Aura", plain("Concentration Aura"), short="Conc"),
                M("Blessing of Kings", buff("Blessing of Kings"),
                  "Class spell at level 20 in Forever (was a Protection talent).", short="BoK"),
            ]),
            G(PANIC, [
                M("Divine Shield (press again to cancel)",
                  "#showtooltip Divine Shield\n/cancelaura Divine Shield\n/cast Divine Shield",
                  "First press bubbles, second press cancels it early.", short="Bubble"),
                M("Divine Protection", plain("Divine Protection"), short="DivProt"),
                M("Lay on Hands self", me("Lay on Hands"), short="LoH me"),
                M("Blessing of Protection self (press again to cancel)",
                  "#showtooltip Blessing of Protection\n/cancelaura Blessing of Protection\n/cast [@player] Blessing of Protection",
                  "BoP stops you from attacking, so the second press removes it.", short="BoP me"),
                M("Voice of Truth", plain("Voice of Truth"),
                  "New in Forever: 6 sec immunity to silence and interrupts. Use before a big heal/cast.", short="VoT"),
            ]),
            G(QOL, [
                M("Seal of Righteousness", plain("Seal of Righteousness"), short="SoR"),
                M("Seal of the Crusader", plain("Seal of the Crusader"), short="SoCru"),
                M("Seal of Wisdom", plain("Seal of Wisdom"), short="SoW"),
                M("Seal of Light", plain("Seal of Light"), short="SoL"),
                M("Seal of Justice", plain("Seal of Justice"), short="SoJ"),
                M("Divine Intervention", heal("Divine Intervention"), short="DI"),
                M("Auras on one button",
                  "#showtooltip [mod:shift] Concentration Aura; [mod:ctrl] Retribution Aura; Devotion Aura\n"
                  "/cast [mod:shift] Concentration Aura; [mod:ctrl] Retribution Aura; Devotion Aura",
                  "Plain click: Devotion. Shift: Concentration. Ctrl: Retribution.", short="Auras"),
            ]),
            G(FOCUS, [
                M("Hammer of Justice focus", foc("Hammer of Justice"), short="HoJ F"),
                M("Turn Undead focus", foc("Turn Undead"), short="TU F"),
            ]),
        ]},

        {"spec": "Tank", "groups": [
            G(DPS, [
                M("Holy Shield", plain("Holy Shield"),
                  "Forever: a 4-charge block buff. Keep it up while tanking.", short="HShield"),
                M("Judgement taunt (mouseover)",
                  "#showtooltip Judgement\n/cast [@mouseover, harm, nodead][harm] Judgement",
                  "With Seal of Fury active, Judgement taunts (10 yd). Hover a loose mob to "
                  "pull it off the healer without changing target.", short="Judge@"),
            ]),
            G(BUFF, [
                M("Seal of Fury", plain("Seal of Fury"),
                  "New tank seal: Holy damage per hit + absorb shield with a shield equipped. "
                  "Makes Judgement a taunt.", short="SoF"),
                M("Righteous Fury", plain("Righteous Fury"), short="RFury"),
                M("Blessing of Sanctuary", buff("Blessing of Sanctuary"), short="Sanc"),
            ]),
            G(PANIC, [
                M("Templar's Bulwark", plain("Templar's Bulwark"),
                  "Talent. Absorb shield equal to your max health for 8 sec (5 min cooldown).", short="Bulwark"),
            ]),
            G(FOCUS, [
                M("Judgement taunt on focus", foc("Judgement"),
                  "With Seal of Fury: taunt your focus (e.g. the add you're watching).", short="Judge F"),
            ]),
        ]},

        {"spec": "DPS", "groups": [
            G(DPS, [
                M("Repentance", dpsHarm("Repentance"), short="Repent"),
            ]),
            G(BUFF, [
                M("Sanctity Aura", plain("Sanctity Aura"), short="SancAura"),
                M("Seal of Command", plain("Seal of Command"), short="SoCmd"),
            ]),
            G(QOL, [
                M("Seal swap: Command <> Righteousness",
                  "#showtooltip\n/castsequence Seal of Command, Seal of Righteousness",
                  BETA + "with the Twist of Light talent, switching seals lets your next swing "
                  "also apply the old seal. Swap between swings.", short="Twist"),
            ]),
            G(FOCUS, [
                M("Repentance focus", foc("Repentance"), short="Repent F"),
            ]),
        ]},

        {"spec": "Healer", "groups": [
            G(HEAL, [
                M("Holy Shock (friend or foe)", util("Holy Shock"),
                  "Heals a friendly mouseover/target, damages an enemy one.", short="HShock"),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # WARRIOR
    # -------------------------------------------------------------------- #
    {"name": "Warrior", "color": "#C79C6E", "sections": [

        {"spec": "General", "groups": [
            G(DPS, [
                M("Heroic Strike / Cleave (Shift)",
                  "#showtooltip [mod:shift] Cleave; Heroic Strike\n"
                  "/startattack [harm]\n"
                  "/cast [mod:shift, harm] Cleave; [harm] Heroic Strike",
                  "Click: Heroic Strike. Shift-click: Cleave (level 20).", short="HS/Cleave"),
                M("Hamstring", melee("Hamstring"), short="Ham"),
                M("Slam", melee("Slam"), "Level 20 in Forever.", short="Slam"),
                M("Execute", melee("Execute"),
                  "Level 24. Target under 20% health; Battle or Berserker Stance.", short="Exe"),
                M("Overpower (to Battle)", stance(1, "Battle Stance", "Overpower", attack=True), short="OP"),
                M("Interrupt (Pummel / Shield Bash)",
                  "#showtooltip\n/startattack [harm]\n/cast [stance:3, harm] Pummel; [harm] Shield Bash",
                  "Pummel in Berserker Stance (level 38), Shield Bash in Battle or Defensive (needs a shield). "
                  "No stance swap: use the stance dance.", short="Kick"),
            ]),
            G(AUTO, [
                M("Ranged weapon (Bow/Gun/Crossbow/Thrown)",
                  "#showtooltip\n/cast [equipped:Thrown] Throw; [equipped:Bows] Shoot Bow; "
                  "[equipped:Guns] Shoot Gun; [equipped:Crossbows] Shoot Crossbow",
                  "One button for whatever ranged weapon you have equipped.", short="Ranged"),
            ]),
            G(PANIC, [
                M("Disarm (to Defensive)", stance(2, "Defensive Stance", "Disarm"), short="Disarm"),
                M("Stance cooldown (Retaliation/Shield Wall/Recklessness)",
                  "#showtooltip [stance:1] Retaliation; [stance:2] Shield Wall; [stance:3] Recklessness\n"
                  "/cast [stance:1] Retaliation; [stance:2] Shield Wall; [stance:3] Recklessness",
                  "Uses the big cooldown of the stance you're in.", short="StanceCD"),
            ]),
            G(QOL, [
                M("Charge / Intercept (one button)",
                  "#showtooltip Charge\n"
                  "/cast [nocombat, nostance:1] Battle Stance; "
                  "[nocombat, @targettarget, harm, exists][nocombat, harm] Charge; "
                  "[nostance:3] Berserker Stance; "
                  "[@targettarget, harm, exists][harm] Intercept",
                  "Out of combat: Charge. In combat: Intercept (level 30). "
                  "Tactical Mastery (now trained) keeps up to 10 rage on a stance swap.", short="Charge"),
                M("Charge + Rend (opener)",
                  "#showtooltip Charge\n"
                  "/startattack [harm]\n"
                  "/cast [nocombat, nostance:1] Battle Stance\n"
                  "/cast [nocombat, harm] Charge\n"
                  "/cast [harm] Rend",
                  "Charges in (out of combat only) then immediately opens with Rend.", short="Charge+Rend"),
                M("Taunt (to Defensive)", stance(2, "Defensive Stance", "Taunt"), "Target the friend being hit: TT is the mob.",
                  short="Taunt"),
                M("Mocking Blow (to Battle)", stance(1, "Battle Stance", "Mocking Blow", attack=True), short="Mock"),
                M("Stance dance (Battle -> Defensive -> Berserker)",
                  "#showtooltip Battle Stance\n"
                  "/cast [stance:1] Defensive Stance; [stance:2] Berserker Stance; [stance:3] Battle Stance",
                  "One button cycles Battle -> Defensive -> Berserker -> Battle.", short="Stances"),
                M("Stance toggle (Battle <> Defensive, mods for others)",
                  "#showtooltip\n/cast [mod:ctrl, nostance:3] Berserker Stance; "
                  "[mod:alt, nostance:2] Defensive Stance; [stance:1] Defensive Stance; Battle Stance",
                  "Click swaps Battle <> Defensive. Ctrl = Berserker (level 30). Alt = Defensive.", short="StanceTog"),
                M("Off-hand <> shield swap",
                  "/equipslot [noequipped:Shields] 17 Your Shield\n/equipslot [equipped:Shields] 17 Your Offhand",
                  "Fill in your own shield and off-hand item names.", short="OHSwap", icon="INV_Shield_06"),
            ]),
            G(FOCUS, [
                M("Interrupt focus (Pummel / Shield Bash)",
                  "#showtooltip\n/cast [stance:3, @focus, harm, exists][stance:3, harm] Pummel; [@focus, harm, exists][harm] Shield Bash",
                  "Interrupts your focus (or your target if you have no focus): Pummel in Berserker Stance, "
                  "Shield Bash in Battle or Defensive (needs a shield). No stance swap.", short="Kick F"),
            ]),
        ]},

        {"spec": "Tank", "groups": [
            G(DPS, [
                M("Victory Rush > Revenge > Sunder Armor",
                  "#showtooltip\n/startattack [harm]\n/cast [harm] Victory Rush\n/cast [harm] Revenge\n/cast [harm] Sunder Armor\n/run UIErrorsFrame:Clear()",
                  "One tank spam button: Victory Rush when it's up after a kill, else Revenge when it's lit "
                  "(after a block, dodge or parry), else Sunder. Use this on trash; the Shield Block version "
                  "on bosses and big pulls. The last line hides the \"not ready\" error.", short="Rev>Sund"),
                M("Shield Block + Revenge > Sunder Armor",
                  "#showtooltip\n/startattack [harm]\n/cast Shield Block\n/cast [harm] Revenge\n/cast [harm] Sunder Armor\n/run UIErrorsFrame:Clear()",
                  BETA + "Shield Block has no global cooldown, so it fires with the next button whenever it's off "
                  "cooldown (needs a shield and Defensive Stance). More blocks = more Revenge procs. Watch your "
                  "rage: Shield Block 10, Sunder 15.", short="SBlk+Sund"),
                M("Concussion Blow", melee("Concussion Blow"), "Talent (in our level-30 tank build).", short="Concuss"),
                M("Shield Slam", melee("Shield Slam"), "Talent, level 40. Forever: about double the damage.", short="SSlam"),
            ]),
            G(QOL, [
                M("Charge (Vanguard, any stance)",
                  "#showtooltip Charge\n/startattack [harm]\n/cast [harm] Charge",
                  "With the Vanguard talent (level-30 tank build) Charge works in Defensive Stance, "
                  "so no stance swap.", short="VCharge"),
                M("Taunt (mouseover)",
                  "#showtooltip Taunt\n/cast [@mouseover, harm, nodead][harm] Taunt",
                  "Defensive Stance. Hover a loose mob to taunt it without changing target.", short="Taunt@"),
            ]),
        ]},

        {"spec": "DPS", "groups": [
            G(DPS, [
                M("Victory Rush > Heroic Strike",
                  "#showtooltip\n/startattack [harm]\n/cast [harm] Victory Rush\n/cast [harm] Heroic Strike",
                  BETA + "Victory Rush when it's up after a kill; Heroic Strike (no global "
                  "cooldown) queues on your next swing either way. Watch your rage.", short="VR>HS"),
                M("Sweeping Strikes (to Battle)", stance(1, "Battle Stance", "Sweeping Strikes", tt=False),
                  "Arms talent (in our level-30 Arms build). Pair with Cleave.", short="Sweep"),
                M("Mortal Strike", melee("Mortal Strike"), "Arms talent, level 40.", short="MS"),
                M("Bloodthirst", melee("Bloodthirst"), "Fury talent, level 40.", short="BT"),
                M("Whirlwind (to Berserker)", stance(3, "Berserker Stance", "Whirlwind", tt=False),
                  "Level 36.", short="WW"),
            ]),
        ]},
    ]},
]
