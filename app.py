import streamlit as st
import pandas as pd
import unicodedata

# --- 1. FONCTION POUR NETTOYER LE TEXTE (Ignorer accents, majuscules...) ---
def nettoyer_texte(texte):
    if pd.isna(texte):
        return ""
    # Convertir en chaîne de caractères, mettre en minuscules et enlever les espaces inutiles
    texte = str(texte).lower().strip()
    # Supprimer les accents
    texte = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
    return texte

# --- 2. INTERFACE DE L'APPLICATION ---
st.set_page_config(page_title="Vérificateur de Leads", layout="wide")
st.title("🔍 Recherche de Restaurants (Acquisition)")
st.write("Vérifiez rapidement si un restaurant existe déjà dans la base principale ou dans les sprints en cours.")

# --- 3. CHARGEMENT DES FICHIERS ---
col1, col2 = st.columns(2)
with col1:
    fichier_base = st.file_uploader("1. Base Principale (CSV point-virgule)", type=["csv"])
with col2:
    fichiers_sprints = st.file_uploader("2. Fichiers Sprint (CSV)", type=["csv"], accept_multiple_files=True)

# --- 4. BARRE DE RECHERCHE ---
st.divider()
recherche = st.text_input("👉 Tapez le nom du restaurant à chercher (ex: tacos de lyon) :")

# --- 5. LOGIQUE DE RECHERCHE ---
if recherche:
    recherche_propre = nettoyer_texte(recherche)
    trouve_quelque_part = False
    
    # A. Recherche dans la base principale
    if fichier_base is not None:
        try:
            # On remet le curseur au début du fichier au cas où on recharge
            fichier_base.seek(0)
            df_base = pd.read_csv(fichier_base, sep=";")
            
            # On nettoie la colonne des noms pour la recherche
            df_base['Nom_Recherche'] = df_base['Restaurant Name'].apply(nettoyer_texte)
            
            # On filtre pour voir si la recherche est contenue dans le nom
            resultats_base = df_base[df_base['Nom_Recherche'].str.contains(recherche_propre, na=False)]
            
            if not resultats_base.empty:
                trouve_quelque_part = True
                st.error(f"🚨 ATTENTION : {len(resultats_base)} résultat(s) trouvé(s) dans la BASE PRINCIPALE !")
                # On n'affiche que les colonnes utiles
                st.dataframe(resultats_base[['Restaurant Name', 'Main City', 'Status', 'phone']], use_container_width=True)
        except Exception as e:
            st.error("Erreur de lecture de la base principale. Vérifiez que c'est bien un fichier CSV avec point-virgule (;).")

    # B. Recherche dans les Sprints
    if fichiers_sprints:
        df_liste_sprints = []
        for f in fichiers_sprints:
            f.seek(0)
            try:
                df = pd.read_csv(f, sep=",")
                df['Fichier_Source'] = f.name.replace("Sales Sprint Avril-Mai (4).xlsx - ", "").replace(".csv", "")
                df_liste_sprints.append(df)
            except:
                pass # Ignore les fichiers qui posent problème
        
        if df_liste_sprints:
            df_tous_sprints = pd.concat(df_liste_sprints, ignore_index=True)
            df_tous_sprints['Nom_Recherche'] = df_tous_sprints['Restaurant'].apply(nettoyer_texte)
            
            resultats_sprints = df_tous_sprints[df_tous_sprints['Nom_Recherche'].str.contains(recherche_propre, na=False)]
            
            if not resultats_sprints.empty:
                trouve_quelque_part = True
                st.warning(f"⚠️ ATTENTION : {len(resultats_sprints)} résultat(s) trouvé(s) dans les SPRINTS EN COURS !")
                st.dataframe(resultats_sprints[['Restaurant', 'Fichier_Source', 'STATUT', 'BINOME']], use_container_width=True)

    # C. Si rien n'est trouvé
    if not trouve_quelque_part and (fichier_base is not None or fichiers_sprints):
        st.success("✅ Aucun restaurant correspondant trouvé. Vous pouvez l'ajouter pour le mois prochain !")
