"""Shared palette catalogue for profile, appearance and rendering.

Les noms affichés sont purement cosmétiques : seules ces étiquettes changent,
les couleurs (valeurs hex) et les clés internes restent identiques. L'ordre de
ce dictionnaire fixe l'ordre d'affichage dans le profil et le menu F2.
"""
PALETTES = {
    'violet':  ('AMÉTHYSTE / SIGNATURE', '#965ff6', '#6c3fd0', '#0e0b16', '#171026', '#39275c', '#efe9fb', '#9a8bb3', '#ffd49b'),
    'rose':    ('PÉTALE / DOUCEUR',      '#ff9fcd', '#aa5982', '#170e14', '#271720', '#573044', '#ffeaf4', '#b696a6', '#e6b8ff'),
    'orchid':  ('ORCHIDÉE / NOCTURNE',   '#c39aff', '#8057c9', '#100d19', '#1c152d', '#392952', '#f0e8fc', '#9b8bad', '#ffb9d7'),
    'ocean':   ('ABYSSE / BLEU PROFOND', '#72a7ff', '#416cb2', '#0a101b', '#111d30', '#263d60', '#e7efff', '#8a9cba', '#9ce6db'),
    'emerald': ('JADE / FORÊT',          '#50e3a4', '#258568', '#0b1310', '#111f19', '#244437', '#e4f7ee', '#8aaa9b', '#e5d298'),
    'amber':   ('AMBRE / OR',            '#ffc766', '#ad7e32', '#14110b', '#211b10', '#49391f', '#fff2d8', '#b5a181', '#ff987a'),
    'glacier': ('GIVRE / PRÉCISION',     '#7be0ff', '#258ba9', '#091016', '#101e27', '#24414d', '#e9f4fa', '#829da9', '#c0bcff'),
    'crimson': ('RUBIS / CLASSIQUE',     '#ff506a', '#b92c45', '#100d13', '#1b121d', '#43202f', '#eee8ef', '#998496', '#ffd49b'),
    'ivory':   ('IVOIRE / NOIR',         '#eadbb9', '#a28b60', '#10100f', '#1d1c19', '#413c30', '#f0ece2', '#a39d8e', '#a9c9bd'),
    'mono':    ('ARGENT / MONOCHROME',   '#e0e5ed', '#89929d', '#101113', '#1b1d20', '#3d4147', '#f4f5f7', '#a0a6ae', '#c9d0da'),
    'rainbow': ('PRISME / SPECTRE',      '#ff506a', '#a33b63', '#0e0d15', '#191621', '#363047', '#f3edff', '#a49bb8', '#ffe3a3'),
}
