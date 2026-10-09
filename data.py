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
                M("Fear Ward", buff("Fear Ward"), "Racial/availability may differ in Forever.", short="FearWard"),
            ]),
            G(PANIC, [
                M("Shield self", me("Power Word: Shield"), short="PWS me"),
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
                M("Prayer of Mending", heal("Prayer of Mending"),
                  "New in Forever. Heals, then jumps to another group member when they take damage.", short="PoM"),
            ]),
        ]},

        {"spec": "Discipline", "groups": [
            G(HEAL, [
                M("Power Infusion", heal("Power Infusion"), short="PowerInf"),
                M("Penance (friend or foe)", util("Penance"),
                  "New in Forever. Heals a friendly mouseover/target, damages an enemy one.", short="Penance"),
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
                M("Drain Life (spam-safe)", chan("Drain Life"), short="DrainLife"),
                M("Drain Soul (spam-safe)", chan("Drain Soul"), short="DrainSoul"),
                M("Drain Mana (spam-safe)", chan("Drain Mana"), short="DrainMana"),
            ]),
            G(AUTO, [
                M("Wand (spam-safe)", WAND, short="Wand"),
            ]),
            G(HEAL, [
                M("Unending Breath", buff("Unending Breath"), short="UnendBreath"),
                M("Detect Invisibility", buff("Detect Invisibility"), short="DetectInv"),
                M("Soulstone mouseover",
                  "/use [@mouseover, help, exists][help] Major Soulstone",
                  "Swap item name to your soulstone rank.", short="Soulstone", icon="INV_Misc_Orb_04"),
            ]),
            G(CLEAN, [
                M("Devour Magic (Felhunter)", heal("Devour Magic"), short="DevourMagic"),
            ]),
            G(QOL, [
                M("Pet attack TT / target", PETATK, short="PetAtk", icon="Ability_GhoulFrenzy"),
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
                M("Wrack (spam-safe)", chan("Wrack"),
                  "New in Forever. Channeled drain that makes the target take more Shadow DoT damage.", short="Wrack"),
                M("Amplify Curse + Agony",
                  "#showtooltip Curse of Agony\n/cast Amplify Curse\n/cast [harm] Curse of Agony", short="AmpCurse"),
                M("DoT sequence (press to roll dots)",
                  "#showtooltip Corruption\n"
                  "/castsequence [harm] reset=target Corruption, Curse of Agony, Siphon Life, Immolate",
                  short="DoTSeq"),
            ]),
        ]},

        {"spec": "Demonology", "groups": [
            G(QOL, [
                M("Fel Domination + Felhunter",
                  "#showtooltip Summon Felhunter\n/cast Fel Domination\n/cast Summon Felhunter", short="FelDom+FH"),
                M("Fel Domination + Voidwalker",
                  "#showtooltip Summon Voidwalker\n/cast Fel Domination\n/cast Summon Voidwalker", short="FelDom+VW"),
            ]),
        ]},

        {"spec": "Destruction", "groups": [
            G(DPS, [
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
                M("Arcane Missiles (spam-safe)", chan("Arcane Missiles"), short="ArcMissiles"),
                M("Frost Nova", "#showtooltip Frost Nova\n/stopcasting\n/cast [harm] Frost Nova",
                  "Clears your current cast first so the root fires instantly.", short="FrostNova"),
                M("Counterspell (interrupt)", "#showtooltip Counterspell\n/stopcasting\n/cast [harm] Counterspell",
                  "Clears your current cast first so the interrupt fires instantly.", short="CSpell"),
                M("Polymorph + Diamond mark",
                  "#showtooltip Polymorph\n/targetmarker [harm] 3\n/cast [harm] Polymorph",
                  "Marks the sheep target with a diamond so the group knows not to break it. "
                  "Uses the full /targetmarker name, not /tm — the ThreatMaster addon claims "
                  "/tm for itself, which silently breaks this macro if you use the short form.",
                  short="Poly+Mark"),
            ]),
            G(BUFF, [
                M("Arcane Intellect", buff("Arcane Intellect"), short="ArcInt"),
                M("Dampen Magic", buff("Dampen Magic"), short="DampenMagic"),
                M("Amplify Magic", buff("Amplify Magic"), short="AmpMagic"),
            ]),
            G(PANIC, [
                M("Ice Block (press again to cancel)",
                  "#showtooltip Ice Block\n/cancelaura Ice Block\n/cast Ice Block",
                  "First press casts Ice Block, second press cancels it early.", short="IceBlock"),
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
                M("Gouge (mouseover)", "#showtooltip Gouge\n/cast [@mouseover, harm, nodead][harm, nodead] Gouge",
                  short="Gouge@"),
                M("Kidney Shot", melee("Kidney Shot"), short="KidneyShot"),
                M("Rupture", melee("Rupture"), short="Rupture"),
                M("Garrote", melee("Garrote"), "Requires stealth.", short="Garrote"),
                M("Ambush", melee("Ambush"), "Requires stealth.", short="Ambush"),
                M("Cheap Shot", melee("Cheap Shot"), "Requires stealth. Classic stunlock opener.", short="CheapShot"),
                M("Kick (mouseover)", "#showtooltip Kick\n/stopcasting\n/cast [@mouseover, harm, nodead][harm, nodead] Kick",
                  "Clears your current cast first so the interrupt fires instantly.", short="Kick@"),
            ]),
            G(AUTO, [
                M("Ranged weapon (Bow/Gun/Crossbow/Thrown)",
                  "#showtooltip\n/cast [equipped:Bows] Shoot Bow; [equipped:Guns] Shoot Gun; "
                  "[equipped:Crossbows] Shoot Crossbow; [equipped:Thrown] Throw",
                  "One button for whatever ranged weapon you have equipped.", short="Ranged"),
            ]),
            G(PANIC, [
                M("Blind (mouseover)", "#showtooltip Blind\n/cast [@mouseover, harm, nodead][harm, nodead] Blind",
                  short="Blind@"),
            ]),
            G(QOL, [
                M("Stealth (no cancel)", "#showtooltip Stealth\n/cast [nostealth] Stealth", "Won't drop you out of stealth if pressed again.",
                  short="Stealth"),
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
                M("Grenade at cursor", "#showtooltip Iron Grenade\n/use [@cursor] Iron Grenade",
                  "Swap the item name for the grenade you carry.", short="Grenade", icon="INV_Misc_Bomb_08"),
                M("Sharpening stone (left = main, right = off hand)",
                  "#showtooltip Rough Sharpening Stone\n/use Rough Sharpening Stone\n/use [button:1] 16; [button:2] 17\n"
                  "/click StaticPopup1Button1",
                  "Swap the item name for the stone you carry. The last line confirms the \"replace enchant\" popup.",
                  short="Stone", icon="INV_Stone_02"),
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
                M("Mutilate", melee("Mutilate"), short="Mutilate"),
                M("Cold Blood + Ambush", "#showtooltip Ambush\n/cast Cold Blood\n/cast [harm] Ambush", "Requires stealth.",
                  short="ColdBlood+Amb"),
            ]),
        ]},

        {"spec": "Subtlety", "groups": [
            G(DPS, [
                M("Hemorrhage", melee("Hemorrhage"), short="Hemo"),
            ]),
        ]},
    ]},

    # -------------------------------------------------------------------- #
    # SHAMAN
    # -------------------------------------------------------------------- #
    {"name": "Shaman", "color": "#0070DE", "sections": [

        {"spec": "Shared", "groups": [
            G(DPS, [
                M("Earth Shock (interrupt)", "#showtooltip Earth Shock\n/stopcasting\n/cast [harm] Earth Shock",
                  "Clears your current cast first so the interrupt fires instantly.", short="EShock"),
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
                M("Water Walking", buff("Water Walking"), short="WaterWalk"),
                M("Water Breathing", buff("Water Breathing"), short="WaterBreath"),
            ]),
            G(PANIC, [
                M("Self Lesser Healing Wave", me("Lesser Healing Wave"), short="SelfLHWave"),
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
            ]),
            G(FOCUS, [
                M("Earth Shock interrupt on focus", "#showtooltip Earth Shock\n/stopcasting\n/cast [@focus, harm, exists][harm] Earth Shock",
                  "Clears your current cast first so the interrupt fires instantly.", short="EShock F"),
                M("Purge focus", foc("Purge"), short="Purge F"),
            ]),
        ]},

        {"spec": "Elemental", "groups": [
            G(DPS, [
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
                M("Stormstrike", melee("Stormstrike"),
                  "Starts auto-attack too. In Forever it boosts only your NEXT Lightning Bolt, "
                  "Chain Lightning or Earth Shock, so follow up with one.", short="Stormstrike"),
            ]),
            G(BUFF, [
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
                M("Hunter's Mark + send pet (opener)",
                  "#showtooltip Hunter's Mark\n/petattack [harm]\n/cast [harm] Hunter's Mark",
                  "One press marks the target and sends the pet in.", short="HMark+Pet"),
                M("Volley at cursor", "#showtooltip Volley\n/cast [@cursor] Volley",
                  "Forever removed Volley's cooldown, so it's a real AoE button now. "
                  "Drops at your mouse cursor, no targeting circle.", short="Volley"),
                M("Raptor Strike + Wing Clip",
                  "#showtooltip Raptor Strike\n/startattack [harm]\n/cast [harm] Raptor Strike\n/cast [harm] Wing Clip", short="Raptor+Clip"),
            ]),
            G(AUTO, [
                M("Auto Shot (spam-safe)",
                  "#showtooltip Auto Shot\n/cast [@targettarget, harm, exists][harm] !Auto Shot",
                  "Hunter exception: ! stops Auto Shot toggling off. Unlike wand Shoot, it works here.",
                  short="AutoShot"),
            ]),
            G(BUFF, [
                M("Aspect: Hawk in combat, Cheetah out",
                  "#showtooltip Aspect of the Hawk\n/cast [combat] Aspect of the Hawk; Aspect of the Cheetah",
                  short="AspectHawk"),
            ]),
            G(PANIC, [
                M("Feign Death (clean)",
                  "#showtooltip Feign Death\n/petfollow\n/stopattack\n/cast Feign Death",
                  "Calls the pet back and stops attacking first, so the pet doesn't keep mobs on you.", short="FeignDeath"),
            ]),
            G(QOL, [
                M("Pet attack mouseover / TT", PETATK_MO_TT,
                  "Mouseover first, then your target's target, then your target. " + PET_ICON_NOTE,
                  short="PetAtkMOTT", icon="Ability_GhoulFrenzy"),
                M("Pet attack / Shift = follow", PETATK_SHIFT,
                  "Press to send the pet (mouseover first); Shift+press calls it back. " + PET_ICON_NOTE,
                  short="PetAtkShift", icon="Ability_GhoulFrenzy"),
                M("Call / Revive / Mend (one button)",
                  "#showtooltip Mend Pet\n/cast [nopet] Call Pet; [@pet, dead] Revive Pet; Mend Pet", short="PetMend"),
                M("Feed Pet",
                  "#showtooltip Feed Pet\n/cast Feed Pet\n/use Tough Jerky",
                  "Swap food item for your pet's diet.", short="FeedPet"),
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
            G(FOCUS, [
                M("Scatter Shot focus", foc("Scatter Shot"), short="ScatterShot F"),
            ]),
        ]},

        {"spec": "Survival", "groups": [
            G(DPS, [
                M("Survival melee button (Raptor + Mongoose + Strider Kick)",
                  "#showtooltip Raptor Strike\n/startattack [harm]\n/cast [harm] Raptor Strike\n"
                  "/cast [harm] Mongoose Bite\n/cast [harm] Strider Kick",
                  BETA + "Raptor Strike queues on your next swing (no global cooldown), then "
                  "Mongoose Bite if it's lit up, else Strider Kick. Spam it in melee.", short="SurvMelee"),
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
                M("Hammer of Justice", dpsMO("Hammer of Justice"),
                  "Stuns whatever's under your mouse without changing your target; "
                  "falls back to your target if nothing's under the mouse.", short="HoJ"),
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
                M("Blessing of Kings", buff("Blessing of Kings"),
                  "Class spell at level 20 in Forever (was a Protection talent).", short="BoK"),
            ]),
            G(PANIC, [
                M("Divine Shield (press again to cancel)",
                  "#showtooltip Divine Shield\n/cancelaura Divine Shield\n/cast Divine Shield",
                  "First press bubbles, second press cancels it early.", short="Bubble"),
                M("Lay on Hands self", me("Lay on Hands"), short="LoH me"),
                M("Blessing of Protection self (press again to cancel)",
                  "#showtooltip Blessing of Protection\n/cancelaura Blessing of Protection\n/cast [@player] Blessing of Protection",
                  "BoP stops you from attacking, so the second press removes it.", short="BoP me"),
            ]),
            G(QOL, [
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
                M("Judgement taunt (mouseover)",
                  "#showtooltip Judgement\n/cast [@mouseover, harm, nodead][harm] Judgement",
                  "With Seal of Fury active, Judgement taunts (10 yd). Hover a loose mob to "
                  "pull it off the healer without changing target.", short="Judge@"),
            ]),
            G(BUFF, [
                M("Blessing of Sanctuary", buff("Blessing of Sanctuary"), short="Sanc"),
            ]),
            G(FOCUS, [
                M("Judgement taunt on focus", foc("Judgement"),
                  "With Seal of Fury: taunt your focus (e.g. the add you're watching).", short="Judge F"),
            ]),
        ]},

        {"spec": "DPS", "groups": [
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
                M("Victory Rush", melee("Victory Rush"),
                  "New in Forever (level 20). Free, any stance, heals 10% of your max health. Only after a kill "
                  "that gives XP (20 sec). Its own button: Forever macros can't fall through to another spell.",
                  short="VR"),
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
                  "#showtooltip Charge(Rank 1)\n"
                  "/cast [nocombat, nostance:1] Battle Stance; "
                  "[nocombat, @targettarget, harm, exists][nocombat, harm] Charge(Rank 1); "
                  "[nostance:3] Berserker Stance; "
                  "[@targettarget, harm, exists][harm] Intercept",
                  "Out of combat: Charge. In combat: Intercept (level 30). "
                  "Tactical Mastery (now trained) keeps up to 10 rage on a stance swap. Rank 1 on purpose: on Forever an unranked \"Charge\" resolves to the level-46 rank (spell 1240289) and fails until you know it (owner test 2026-10-09).", short="Charge"),
                M("Charge + Rend (opener)",
                  "#showtooltip Charge(Rank 1)\n"
                  "/startattack [harm]\n"
                  "/cast [nocombat, nostance:1] Battle Stance\n"
                  "/cast [nocombat, harm] Charge(Rank 1)\n"
                  "/cast [harm] Rend",
                  "Charges in (out of combat only) then opens with Rend. Rank 1 on purpose: on Forever an unranked \"Charge\" resolves to the level-46 rank (spell 1240289) and fails until you know it (owner test 2026-10-09).", short="Charge+Rend"),
                M("Taunt (to Defensive)", stance(2, "Defensive Stance", "Taunt"), "Target the friend being hit: TT is the mob.",
                  short="Taunt"),
                M("Mocking Blow (to Battle)", stance(1, "Battle Stance", "Mocking Blow", attack=True), short="Mock"),
                M("Stance swap (Battle <> Defensive)",
                  "#showtooltip [stance:1] Defensive Stance; Battle Stance\n"
                  "/cast [stance:1] Defensive Stance; Battle Stance",
                  "One button swaps Battle <> Defensive (from Berserker or no stance it goes to Battle). "
                  "Only two stances on purpose: a three-stance cycle gets stuck in Defensive Stance before "
                  "level 30, because Berserker Stance isn't learned yet.", short="Stances"),
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
                M("Sunder Armor", melee("Sunder Armor"),
                  "Your spam button. Starts auto-attack.", short="Sunder"),
                M("Revenge", melee("Revenge"),
                  "Defensive Stance, after a block, dodge or parry: press it whenever it lights up "
                  "(best threat per rage). Its own button because Forever macros stop at the first spell you know but can't use right now, so \"Revenge, else Sunder\" never reaches Sunder (tested 2026-10-09).", short="Rev"),
                M("Shield Block + Sunder Armor",
                  "#showtooltip Shield Block\n/startattack [harm]\n/cast Shield Block\n/cast [harm] Sunder Armor",
                  BETA + "Shield Block is off the global cooldown, so it fires with Sunder in one press. "
                  "Unknown on Forever: whether Sunder still goes out while Shield Block is on cooldown "
                  "(if not, use plain Sunder between blocks). Needs a shield and Defensive Stance.", short="SBlk+Sund"),
                M("Shield Block + Revenge",
                  "#showtooltip Shield Block\n/startattack [harm]\n/cast Shield Block\n/cast [harm] Revenge",
                  BETA + "Shield Block is off the global cooldown, so it fires with Revenge in one press. "
                  "Forever stops a macro at the first spell you know but can't use right now, so while Shield Block "
                  "is on cooldown Revenge will not go out from this button: use the plain Revenge button then. "
                  "Needs a shield and Defensive Stance.", short="SBlk+Rev"),
                M("Concussion Blow", melee("Concussion Blow"), "Talent (in our level-30 tank build).", short="Concuss"),
                M("Shield Slam", melee("Shield Slam"), "Talent, level 40. Forever: about double the damage.", short="SSlam"),
            ]),
            G(QOL, [
                M("Charge + Rend (Vanguard, any stance)",
                  "#showtooltip Charge(Rank 1)\n/startattack [harm]\n"
                  "/cast [nocombat, harm] Charge(Rank 1)\n/cast [harm] Rend",
                  "With the Vanguard talent (level-30 tank build) Charge works in Defensive Stance, "
                  "so no stance swap. Out of combat it charges, then press again for Rend (it fails while you are "
                  "still out of range). Rank 1 on purpose: on Forever an unranked \"Charge\" resolves to the level-46 rank (spell 1240289) and fails until you know it (owner test 2026-10-09).", short="VCharge"),
                M("Taunt (mouseover)",
                  "#showtooltip Taunt\n/cast [@mouseover, harm, nodead][harm] Taunt",
                  "Defensive Stance. Hover a loose mob to taunt it without changing target.", short="Taunt@"),
            ]),
        ]},

        {"spec": "DPS", "groups": [
            G(DPS, [
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
