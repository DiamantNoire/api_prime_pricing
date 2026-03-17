# - /src/config.py

# Importation de librairies
import os
from zoneinfo import ZoneInfo
import dotenv
from pydantic import HttpUrl
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union

# Chargement:
dotenv.load_dotenv()

# Classe des variables d'environnement
@dataclass
class Config:
    # Utilisateurs:
    UTILISATEUR_0 = "Charly"

    # Titre des pages:
    TITRE_PAGE_0 = "Acceuil - Supervision JDD ODRE"
    TITRE_PAGE_1 = "Surveillance des flux"
    TITRE_PAGE_2 = "Alertes et notififcaitons"
    TITRE_PAGE_3 = "Qualité de la donnée"
    TITRE_PAGE_4 = "Actualisation des données"
    TITRE_PAGE_5 = "Gestion des référentiels"

    # Chemin du style css:
    PATH_CSS = r"C:\Users\\0471IA\OneDrive - NaTran\_1_Outils de supervision JDD ODRE\_7_Streamlit_app\src\interface_utilisateurs\custom.css"

    #Base url métadata
    BASE_URL = "https://odre.opendatasoft.com/api/automation/v1.0/datasets"
    PREFIX = "https://stagrtsysinfprdweodap.blob.core.windows.net/opendata"

    PROXIES = {}
    TIMEOUT: int = 15
    TIMEOUT_CONNECT = (15.0, 20.0)
    LIMIT = 1000
    TRY_CALL = 3
    BACKOFT_FACT = 0.5
    VERIFY_SSL = True
    TRY_CODE = [429, 500, 502, 503, 504]
    
    # Clé Api admin opendata
    API_KEY = "8fb4872417d95f8b75a5ed83738c053d6b12817bc82af9b9cf05ae04"

    # Clés possible de stockages des données dans l'api
    CANDIDATE_KEYS = ["data", "results", "records", "items"]

    # Gestion des erreus https
    CODE_ERREUR_HTTPS = [429, 500, 502, 503, 504]

    # Chemin excel blob_monitoring
    PATH_BLOB_MONITORING = r"C:\Users\\0471IA\OneDrive - NaTran\_1_Outils de supervision JDD ODRE\_3_Streamlit_app\input\MonitorBlob.xlsx"
    FEUILLE_CIBLE_BLOB_MONITORING = "MonitorBlob(app)"

    # Chemin vers la base en local avant passage dans snowflake
    DB_PATH = r"db/db_local_v1.db"

    # Format de compression Parquet
    PARQUET_FORMAT_COMPRESSION = {
        "SNAPPY": "snappy",
        "GZIP": "gzip", 
        "BROTLI": "brotli",
        "LZ4": "lz4",
        "ZSTD": "zstd",
    }

    # Utile pour typer le json récupéré après appel api sur les métadata des JDD ODRE
    JDD_ODRE_PATH_PARQUET = r"src\data\JDD_ODRE.parquet"
    JDD_ODRE_CSV_PARQUET = r"src\data\JDD_ODRE.csv"
    JDD_ODRE_JSON_PARQUET = r"src\data\JDD_ODRE.json"

    # Cache des JDD (parquet)
    ENABLE_CACHE_JDD = True
    CACHE_TTL_MINUTES_JDD = 60
    # Forcer la lecture du parquet s'il existe (phase de tests)
    FORCE_READ_PARQUET_ALWAYS = True

    # Pour désérealiser les json imbriqués dans le fichier parquet en local qui modélise les jdds
    
    LISTE_COLS_JSON_RESSOURCES = ["ressources_json"]
    LISTE_COLS_JSON_PDA = ["matched_blobs_json"]


    #METADATA_JDD_ODRE_PATH_JSON = r"src/data/metadata_JDD_ODRE.parquet"
    METADATA_JDD_ODRE_PATH_PARQUET = r"src/data/metadata_JDD_ODRE.parquet"
    CHAMPS_OBLIGATOIRE_META = [ "dataset_id","is_published","is_restricted", "created_at", "updated_at"]
    LISTE_CHAMPS_META = ['uid', 'dataset_id', 'is_published', 'is_restricted', 'created_at', 'updated_at', 'asset_type', 'default_security_is_data_visible', 'default_security_visible_fields', 'default_security_filter_query', 'default_security_api_calls_quota', 'metadata_visualization_analyze_disabled_value', 'metadata_visualization_analyze_default_value', 'metadata_visualization_table_fields_value', 'metadata_visualization_table_default_sort_field_value', 'metadata_visualization_table_default_sort_direction_value', 'metadata_visualization_map_disabled_value', 'metadata_visualization_map_marker_hidemarkershape_value', 'metadata_visualization_map_tooltip_disabled_value', 'metadata_visualization_map_tooltip_html_enabled_value', 'metadata_visualization_images_disabled_value', 'metadata_visualization_image_tooltip_html_enabled_value', 'metadata_visualization_calendar_enabled_value', 'metadata_visualization_calendar_tooltip_html_enabled_value', 'metadata_visualization_custom_view_enabled_value', 'metadata_internal_metadata_source_language_value', 'metadata_internal_license_id_value', 'metadata_internal_theme_id_value', 'metadata_internal_draft_value', 'metadata_default_modified_value', 'metadata_default_language_value', 'metadata_default_title_value', 'metadata_default_description_value', 'metadata_default_keyword_value', 'metadata_default_timezone_value', 'metadata_default_modified_updates_on_metadata_change_value', 'metadata_default_modified_updates_on_data_change_value', 'metadata_default_geographic_reference_auto_value', 'metadata_default_publisher_value', 'metadata_custom_maille_geographique_value', 'metadata_custom_pas_temporel_value', 'metadata_custom_profondeur_dhistorique_value', 'metadata_custom_reseaux_value', 'metadata_custom_energie_value', 'metadata_admin_gestionnaire_technique_de_la_donnee_value', 'metadata_admin_gestionnaire_metier_de_la_donnee_value', 'metadata_admin_direction_metier_concernee_value', 'metadata_admin_tags_value', 'metadata_admin_type_de_source_de_donnees_value', 'metadata_admin_source_de_la_donnee_value', 'metadata_admin_sla_value', 'metadata_admin_enjeux_value', 'metadata_admin_theme_value', 'metadata_dcat_contact_name_value', 'metadata_dcat_contact_email_value', 'metadata_dcat_accrualperiodicity_value', 'metadata_asset_content_configuration_facets_value', 'metadata_asset_content_configuration_is_explore_data_with_ai_disabled_value', 'metadata_visualization_map_marker_color_value', 'metadata_visualization_map_tooltip_title_value', 'metadata_visualization_map_tooltip_fields_value', 'metadata_visualization_map_tooltip_sort_field_value', 'metadata_visualization_custom_view_html_value', 'metadata_visualization_custom_view_css_value', 'metadata_visualization_custom_view_icon_value', 'metadata_visualization_custom_view_title_value', 'metadata_visualization_map_marker_picto_value', 'metadata_custom_secteur_dactivite_value', 'metadata_visualization_calendar_event_title_value', 'metadata_visualization_calendar_event_start_value', 'metadata_visualization_calendar_event_end_value', 'metadata_visualization_calendar_event_color_value', 'metadata_visualization_calendar_available_views_value', 'metadata_visualization_calendar_default_view_value', 'metadata_default_references_value', 'default_security_api_calls_quota_unit', 'default_security_api_calls_quota_limit', 'metadata_custom_frequence_de_mise_a_jour_value', 'metadata_custom_version_value', 'metadata_default_attributions_value', 'metadata_default_update_frequency_value', 'metadata_visualization_map_tooltip_sort_direction_value', 'metadata_visualization_map_tooltip_html_value', 'metadata_default_geographic_reference_value', 'metadata_visualization_map_basemap_value', 'metadata_dcat_temporal_coverage_start_value', 'metadata_dcat_temporal_coverage_end_value', 'metadata_visualization_custom_view_slug_value', 'metadata_visualization_analyze_disabled_override_remote_value', 'metadata_visualization_analyze_disabled_remote_value', 'metadata_visualization_table_fields_override_remote_value', 'metadata_visualization_table_fields_remote_value', 'metadata_visualization_table_default_sort_field_override_remote_value', 'metadata_visualization_table_default_sort_field_remote_value', 'metadata_visualization_map_disabled_override_remote_value', 'metadata_visualization_map_disabled_remote_value', 'metadata_visualization_map_marker_hidemarkershape_override_remote_value', 'metadata_visualization_map_marker_hidemarkershape_remote_value', 'metadata_visualization_map_tooltip_disabled_override_remote_value', 'metadata_visualization_map_tooltip_disabled_remote_value', 'metadata_visualization_map_tooltip_html_enabled_override_remote_value', 'metadata_visualization_map_tooltip_html_enabled_remote_value', 'metadata_visualization_images_disabled_override_remote_value', 'metadata_visualization_images_disabled_remote_value', 'metadata_visualization_image_tooltip_html_enabled_override_remote_value', 'metadata_visualization_image_tooltip_html_enabled_remote_value', 'metadata_visualization_calendar_enabled_override_remote_value', 'metadata_visualization_calendar_enabled_remote_value', 'metadata_visualization_calendar_tooltip_html_enabled_override_remote_value', 'metadata_visualization_calendar_tooltip_html_enabled_remote_value', 'metadata_visualization_custom_view_enabled_override_remote_value', 'metadata_visualization_custom_view_enabled_remote_value', 'metadata_internal_metadata_source_language_override_remote_value', 'metadata_internal_metadata_source_language_remote_value', 'metadata_internal_license_id_override_remote_value', 'metadata_internal_license_id_remote_value', 'metadata_internal_theme_id_override_remote_value', 'metadata_internal_theme_id_remote_value', 'metadata_default_modified_override_remote_value', 'metadata_default_modified_remote_value', 'metadata_default_geographic_reference_override_remote_value', 'metadata_default_geographic_reference_remote_value', 'metadata_default_language_override_remote_value', 'metadata_default_language_remote_value', 'metadata_default_license_override_remote_value', 'metadata_default_license_remote_value', 'metadata_default_license_value', 'metadata_default_license_url_override_remote_value', 'metadata_default_license_url_remote_value', 'metadata_default_license_url_value', 'metadata_default_title_override_remote_value', 'metadata_default_title_remote_value', 'metadata_default_description_override_remote_value', 'metadata_default_description_remote_value', 'metadata_default_keyword_override_remote_value', 'metadata_default_keyword_remote_value', 'metadata_default_timezone_override_remote_value', 'metadata_default_timezone_remote_value', 'metadata_default_modified_updates_on_metadata_change_override_remote_value', 'metadata_default_modified_updates_on_metadata_change_remote_value', 'metadata_default_modified_updates_on_data_change_override_remote_value', 'metadata_default_modified_updates_on_data_change_remote_value', 'metadata_default_geographic_reference_auto_override_remote_value', 'metadata_default_geographic_reference_auto_remote_value', 'metadata_default_publisher_override_remote_value', 'metadata_default_publisher_remote_value', 'metadata_default_attributions_override_remote_value', 'metadata_default_attributions_remote_value', 'metadata_custom_maille_geographique_override_remote_value', 'metadata_custom_maille_geographique_remote_value', 'metadata_custom_pas_temporel_override_remote_value', 'metadata_custom_pas_temporel_remote_value', 'metadata_custom_profondeur_dhistorique_override_remote_value', 'metadata_custom_profondeur_dhistorique_remote_value', 'metadata_custom_reseaux_override_remote_value', 'metadata_custom_reseaux_remote_value', 'metadata_custom_energie_override_remote_value', 'metadata_custom_energie_remote_value', 'metadata_custom_frequence_de_mise_a_jour_override_remote_value', 'metadata_custom_frequence_de_mise_a_jour_remote_value', 'metadata_custom_secteur_dactivite_override_remote_value', 'metadata_custom_secteur_dactivite_remote_value', 'metadata_dcat_creator_override_remote_value', 'metadata_dcat_creator_remote_value', 'metadata_dcat_creator_value', 'metadata_dcat_contributor_override_remote_value', 'metadata_dcat_contributor_remote_value', 'metadata_dcat_contributor_value', 'metadata_dcat_contact_name_override_remote_value', 'metadata_dcat_contact_name_remote_value', 'metadata_dcat_contact_email_override_remote_value', 'metadata_dcat_contact_email_remote_value', 'metadata_dcat_accrualperiodicity_override_remote_value', 'metadata_dcat_accrualperiodicity_remote_value', 'metadata_dcat_spatial_override_remote_value', 'metadata_dcat_spatial_remote_value', 'metadata_dcat_spatial_value', 'metadata_dcat_temporal_override_remote_value', 'metadata_dcat_temporal_remote_value', 'metadata_dcat_temporal_value', 'metadata_dcat_ap_title_override_remote_value', 'metadata_dcat_ap_title_remote_value', 'metadata_dcat_ap_title_value', 'metadata_dcat_ap_description_override_remote_value', 'metadata_dcat_ap_description_remote_value', 'metadata_dcat_ap_description_value', 'metadata_dcat_ap_keyword_override_remote_value', 'metadata_dcat_ap_keyword_remote_value', 'metadata_dcat_ap_keyword_value', 'metadata_dcat_ap_publisher_name_override_remote_value', 'metadata_dcat_ap_publisher_name_remote_value', 'metadata_dcat_ap_publisher_name_value', 'metadata_asset_content_configuration_facets_override_remote_value', 'metadata_asset_content_configuration_facets_remote_value', 'metadata_visualization_image_title_value', 'metadata_visualization_map_marker_picto_override_remote_value', 'metadata_visualization_map_marker_picto_remote_value', 'metadata_visualization_map_marker_color_override_remote_value', 'metadata_visualization_map_marker_color_remote_value', 'metadata_visualization_map_tooltip_fields_override_remote_value', 'metadata_visualization_map_tooltip_fields_remote_value', 'metadata_default_references_override_remote_value', 'metadata_default_references_remote_value', 'metadata_dcat_publisher_type_override_remote_value', 'metadata_dcat_publisher_type_remote_value', 'metadata_dcat_publisher_type_value', 'metadata_visualization_analyze_default_override_remote_value', 'metadata_visualization_analyze_default_remote_value', 'metadata_visualization_table_default_sort_direction_override_remote_value', 'metadata_visualization_table_default_sort_direction_remote_value', 'metadata_dcat_ap_contact_name_value', 'metadata_dcat_ap_contact_email_value', 'metadata_dcat_created_value', 'metadata_dcat_issued_value', 'metadata_internal_category_id_value', 'metadata_asset_content_configuration_records_search_boosts_value_id', 'metadata_asset_content_configuration_records_search_boosts_value_niveau_tension', 'ressources_json']
    TYPE_MAPPING_METADTA_JDD_ODRE = {

        "uid": Optional[str],
        "dataset_id": Optional[str],
        "is_published": Optional[str],
        "is_restricted": Optional[str],
        "created_at": Optional[str],
        "updated_at": Optional[str],
        "asset_type": Optional[str],
        
        "default_security_is_data_visible": Optional[str],
        "default_security_visible_fields": Optional[str],
        "default_security_filter_query": Optional[str],
        "default_security_api_calls_quota": Optional[str],
        
        "metadata_visualization_analyze_disabled_value": Optional[str],
        "metadata_visualization_analyze_default_value": Optional[str],
        "metadata_visualization_table_fields_value": Optional[str],

        "metadata_visualization_table_default_sort_field_value": Optional[str],
        "metadata_visualization_table_default_sort_direction_value": Optional[str],

        "metadata_visualization_map_disabled_value": Optional[str],
        "metadata_visualization_map_marker_hidemarkershape_value": Optional[str],
        "metadata_visualization_map_tooltip_disabled_value": Optional[str],
        "metadata_visualization_map_tooltip_html_enabled_value": Optional[str],
        "metadata_visualization_images_disabled_value": Optional[str],
        "metadata_visualization_image_tooltip_html_enabled_value": Optional[str],
        "metadata_visualization_calendar_enabled_value": Optional[str],
        "metadata_visualization_calendar_tooltip_html_enabled_value": Optional[str],
        "metadata_visualization_custom_view_enabled_value": Optional[str],
        
        "metadata_internal_metadata_source_language_value": Optional[str],
        "metadata_internal_license_id_value": Optional[str],
        "metadata_internal_theme_id_value": Optional[str],
        "metadata_internal_draft_value": Optional[str],
        
        "metadata_default_title_value": Optional[str],
        "metadata_default_modified_value": Optional[str],
        "metadata_default_modified_updates_on_metadata_change_value": Optional[str],
        "metadata_default_modified_updates_on_data_change_value": Optional[str],
        "metadata_default_geographic_reference_auto_value": Optional[str],
        "metadata_default_language_value": Optional[str],
        "metadata_default_description_value": Optional[str],
        "metadata_default_keyword_value": Optional[str],
        "metadata_default_timezone_value": Optional[str],
        "metadata_default_publisher_value": Optional[str],
        
        "metadata_custom_maille_geographique_value": Optional[str],
        "metadata_custom_pas_temporel_value": Optional[str],
        "metadata_custom_profondeur_dhistorique_value": Optional[str],
        "metadata_custom_reseaux_value": Optional[str],
        "metadata_custom_energie_value": Optional[str],
        
        "metadata_admin_gestionnaire_technique_de_la_donnee_value": Optional[str],
        "metadata_admin_gestionnaire_metier_de_la_donnee_value": Optional[str],
        "metadata_admin_direction_metier_concernee_value": Optional[str],
        "metadata_admin_tags_value": Optional[str],
        "metadata_admin_type_de_source_de_donnees_value": Optional[str],
        "metadata_admin_source_de_la_donnee_value": Optional[str],
        "metadata_admin_sla_value": Optional[str],
        "metadata_admin_enjeux_value": Optional[str],
        "metadata_admin_theme_value": Optional[str],
        
        "metadata_dcat_contact_name_value": Optional[str],
        "metadata_dcat_contact_email_value": Optional[str],
        "metadata_dcat_accrualperiodicity_value": Optional[str],
        
        "metadata_asset_content_configuration_facets_value": Optional[list[dict]],
        "metadata_asset_content_configuration_is_explore_data_with_ai_disabled_value": Optional[str],
        
        "metadata_visualization_map_marker_color_value": Optional[str],
        "metadata_visualization_map_tooltip_title_value": Optional[str],
        "metadata_visualization_map_tooltip_fields_value": Optional[str],
        "metadata_visualization_map_tooltip_sort_field_value": Optional[str],
        "metadata_visualization_custom_view_html_value": Optional[str],
        "metadata_visualization_custom_view_css_value": Optional[str],
        "metadata_visualization_custom_view_icon_value": Optional[str],
        "metadata_visualization_custom_view_title_value": Optional[str],

        "metadata_visualization_map_marker_picto_value": Optional[str],
        "metadata_visualization_map_marker_picto_override_remote_value": Optional[str],
        
        "metadata_custom_secteur_dactivite_value": Optional[str],
        
        "metadata_visualization_calendar_event_title_value": Optional[str],
        "metadata_visualization_calendar_event_start_value": Optional[str],
        "metadata_visualization_calendar_event_end_value": Optional[str],
        "metadata_visualization_calendar_event_color_value": Optional[str],
        "metadata_visualization_calendar_available_views_value": Optional[str],
        "metadata_visualization_calendar_default_view_value": Optional[str],
        
        "metadata_default_references_value": Optional[str],
        
        "default_security_api_calls_quota_unit": Optional[str],
        "default_security_api_calls_quota_limit": Optional[str],
        
        "metadata_custom_frequence_de_mise_a_jour_value": Optional[str],
        "metadata_custom_version_value": Optional[str],
        
        "metadata_default_attributions_value": Optional[str],
        "metadata_default_update_frequency_value": Optional[str],
        
        "metadata_visualization_map_tooltip_sort_direction_value": Optional[str],
        "metadata_visualization_map_tooltip_html_value": Optional[str],
        
        "metadata_default_geographic_reference_value": Optional[str],
        
        "metadata_visualization_map_basemap_value": Optional[str],
        
        "metadata_dcat_temporal_coverage_start_value": Optional[str],
        "metadata_dcat_temporal_coverage_end_value": Optional[str],
        
        "metadata_visualization_custom_view_slug_value": Optional[str],

        "metadata_visualization_analyze_disabled_override_remote_value": Optional[str],
        "metadata_visualization_analyze_disabled_remote_value": Optional[str],

        "metadata_visualization_table_fields_override_remote_value": Optional[str],
        "metadata_visualization_table_fields_remote_value": Optional[str],

        "metadata_visualization_table_default_sort_field_override_remote_value": Optional[str],
        "metadata_visualization_table_default_sort_field_remote_value": Optional[str],

        "metadata_visualization_map_disabled_override_remote_value": Optional[str],
        "metadata_visualization_map_disabled_remote_value": Optional[str],
        "metadata_visualization_map_marker_hidemarkershape_override_remote_value": Optional[str],
        "metadata_visualization_map_marker_hidemarkershape_remote_value": Optional[str],
        "metadata_visualization_map_tooltip_disabled_override_remote_value": Optional[str],
        "metadata_visualization_map_tooltip_disabled_remote_value": Optional[str],
        "metadata_visualization_map_tooltip_html_enabled_override_remote_value": Optional[str],
        "metadata_visualization_map_tooltip_html_enabled_remote_value": Optional[str],

        "metadata_visualization_images_disabled_override_remote_value": Optional[str],
        "metadata_visualization_images_disabled_remote_value": Optional[str],
        "metadata_visualization_image_tooltip_html_enabled_override_remote_value": Optional[str],
        "metadata_visualization_image_tooltip_html_enabled_remote_value": Optional[str],

        "metadata_visualization_calendar_enabled_override_remote_value": Optional[str],
        "metadata_visualization_calendar_enabled_remote_value": Optional[str],
        "metadata_visualization_calendar_tooltip_html_enabled_override_remote_value": Optional[str],
        "metadata_visualization_calendar_tooltip_html_enabled_remote_value": Optional[str],

        "metadata_visualization_custom_view_enabled_override_remote_value": Optional[str],
        "metadata_visualization_custom_view_enabled_remote_value": Optional[str],
        
        "metadata_internal_metadata_source_language_override_remote_value": Optional[str],
        "metadata_internal_metadata_source_language_remote_value": Optional[str],

        "metadata_internal_license_id_override_remote_value": Optional[str],
        "metadata_internal_license_id_remote_value": Optional[str],

        "metadata_internal_theme_id_override_remote_value": Optional[str],
        "metadata_internal_theme_id_remote_value": Optional[str],
        
        "metadata_default_title_override_remote_value": Optional[str],
        "metadata_default_title_remote_value": Optional[str],

        "metadata_default_modified_override_remote_value": Optional[str],
        "metadata_default_modified_remote_value": Optional[str],
        "metadata_default_modified_updates_on_metadata_change_override_remote_value": Optional[str],
        "metadata_default_modified_updates_on_metadata_change_remote_value": Optional[str],
        "metadata_default_modified_updates_on_data_change_override_remote_value": Optional[str],
        "metadata_default_modified_updates_on_data_change_remote_value": Optional[str],

        "metadata_default_geographic_reference_override_remote_value": Optional[str],
        "metadata_default_geographic_reference_remote_value": Optional[str],

        "metadata_default_geographic_reference_auto_override_remote_value": Optional[str],
        "metadata_default_geographic_reference_auto_remote_value": Optional[str],

        "metadata_default_language_override_remote_value": Optional[str],
        "metadata_default_language_remote_value": Optional[str],

        "metadata_default_license_override_remote_value": Optional[str],
        "metadata_default_license_remote_value": Optional[str],
        "metadata_default_license_value": Optional[str],
        "metadata_default_license_url_override_remote_value": Optional[str],
        "metadata_default_license_url_remote_value": Optional[str],
        "metadata_default_license_url_value": Optional[str],

        "metadata_default_description_override_remote_value": Optional[str],
        "metadata_default_description_remote_value": Optional[str],

        "metadata_default_keyword_override_remote_value": Optional[str],
        "metadata_default_keyword_remote_value": Optional[str],

        "metadata_default_timezone_override_remote_value": Optional[str],
        "metadata_default_timezone_remote_value": Optional[str],

        "metadata_default_publisher_override_remote_value": Optional[str],
        "metadata_default_publisher_remote_value": Optional[str],

        "metadata_default_attributions_override_remote_value": Optional[str],
        "metadata_default_attributions_remote_value": Optional[str],
        
        "metadata_custom_maille_geographique_override_remote_value": Optional[str],
        "metadata_custom_maille_geographique_remote_value": Optional[str],

        "metadata_custom_pas_temporel_override_remote_value": Optional[str],
        "metadata_custom_pas_temporel_remote_value": Optional[str],

        "metadata_custom_profondeur_dhistorique_override_remote_value": Optional[str],
        "metadata_custom_profondeur_dhistorique_remote_value": Optional[str],

        "metadata_custom_reseaux_override_remote_value": Optional[str],
        "metadata_custom_reseaux_remote_value": Optional[str],

        "metadata_custom_energie_override_remote_value": Optional[str],
        "metadata_custom_energie_remote_value": Optional[str],

        "metadata_custom_frequence_de_mise_a_jour_override_remote_value": Optional[str],
        "metadata_custom_frequence_de_mise_a_jour_remote_value": Optional[str],

        "metadata_custom_secteur_dactivite_override_remote_value": Optional[str],
        "metadata_custom_secteur_dactivite_remote_value": Optional[str],
        
        "metadata_dcat_creator_override_remote_value": Optional[str],
        "metadata_dcat_creator_remote_value": Optional[str],
        "metadata_dcat_creator_value": Optional[str],

        "metadata_dcat_contributor_override_remote_value": Optional[str],
        "metadata_dcat_contributor_remote_value": Optional[str],
        "metadata_dcat_contributor_value": Optional[str],

        "metadata_dcat_contact_name_override_remote_value": Optional[str],
        "metadata_dcat_contact_name_remote_value": Optional[str],
        "metadata_dcat_contact_email_override_remote_value": Optional[str],
        "metadata_dcat_contact_email_remote_value": Optional[str],

        "metadata_dcat_accrualperiodicity_override_remote_value": Optional[str],
        "metadata_dcat_accrualperiodicity_remote_value": Optional[str],

        "metadata_dcat_spatial_override_remote_value": Optional[str],
        "metadata_dcat_spatial_remote_value": Optional[str],
        "metadata_dcat_spatial_value": Optional[str],

        "metadata_dcat_temporal_override_remote_value": Optional[str], 
        "metadata_dcat_temporal_remote_value": Optional[str],
        "metadata_dcat_temporal_value": Optional[str],

        "metadata_dcat_ap_title_override_remote_value": Optional[str],
        "metadata_dcat_ap_title_remote_value": Optional[str],
        "metadata_dcat_ap_title_value": Optional[str],

        "metadata_dcat_ap_description_override_remote_value": Optional[str],
        "metadata_dcat_ap_description_remote_value": Optional[str],
        "metadata_dcat_ap_description_value": Optional[str],

        "metadata_dcat_ap_keyword_override_remote_value": Optional[str],
        "metadata_dcat_ap_keyword_remote_value": Optional[str],
        "metadata_dcat_ap_keyword_value": Optional[str],

        "metadata_dcat_ap_publisher_name_override_remote_value": Optional[str],
        "metadata_dcat_ap_publisher_name_remote_value": Optional[str],
        "metadata_dcat_ap_publisher_name_value": Optional[str],
        
        "metadata_asset_content_configuration_facets_override_remote_value": Optional[str],
        "metadata_asset_content_configuration_facets_remote_value": Optional[list[dict]],
        
        "metadata_visualization_image_title_value": Optional[str],
        "metadata_visualization_map_marker_picto_remote_value": Optional[str],
        "metadata_visualization_map_marker_color_override_remote_value": Optional[str],
        "metadata_visualization_map_marker_color_remote_value": Optional[str],
        "metadata_visualization_map_tooltip_fields_override_remote_value": Optional[str],
        "metadata_visualization_map_tooltip_fields_remote_value": Optional[str],
        
        "metadata_default_references_override_remote_value": Optional[str],
        "metadata_default_references_remote_value": Optional[str],
        
        "metadata_dcat_publisher_type_override_remote_value": Optional[str],
        "metadata_dcat_publisher_type_remote_value": Optional[str],
        "metadata_dcat_publisher_type_value": Optional[str],
        
        "metadata_visualization_analyze_default_override_remote_value": Optional[str],
        "metadata_visualization_analyze_default_remote_value": Optional[str],
        "metadata_visualization_table_default_sort_direction_override_remote_value": Optional[str],
        "metadata_visualization_table_default_sort_direction_remote_value": Optional[str],
        
        "metadata_dcat_ap_contact_name_value": Optional[str],
        "metadata_dcat_ap_contact_email_value": Optional[str],
        "metadata_dcat_created_value": Optional[str],
        "metadata_dcat_issued_value": Optional[str],
        
        "metadata_internal_category_id_value": Optional[str],
        
        "metadata_asset_content_configuration_records_search_boosts_value_id": Optional[str],
        "metadata_asset_content_configuration_records_search_boosts_value_niveau_tension": Optional[str]
    }
    
    #RESSOURCE_JDD_ODRE_PATH_JSON = r"src/data/ressource_JDD_ODRE.json"
    RESSOURCE_JDD_ODRE_PATH_PARQUET = r"src/data/ressource_JDD_ODRE.parquet"
    CHAMPS_OBLIGATOIRE_RESSOURCES = [ "dataset_id","is_published","is_restricted"]
    LISTE_CHAMPS_RESSOURCES = ['uid', 'title', 'type', 'updated_at', 'display_name', 'datasource_type', 'datasource_file_uid', 'params_headers_first_row', 'params_encoding', 'params_separator', 'params_first_row_no', 'origin_label', 'origin_type', 'extraction_infos_label', 'extraction_infos_type', 'params_doublequote', 'uid_metadata', 'params_sheet_no', 'datasource_connection_uid', 'datasource_relative_url', 'params_extract_meta', 'params_extract_geopoint', 'datasource_headers', 'params_json_root', 'params_json_object', 'params_extract_filename', 'extraction_infos', 'datasource_domain_domain_id', 'datasource_dataset_dataset_id', 'datasource_permissions_user_username', 'url', 'datasource', 'params_interop_metadata', 'params_custom_metadata', 'params_dataset_stats', 'params_private_datasets', 'params_staged_datasets', 'params_admin_metadata', 'apikey', 'push_url', 'enabled', 'params_bootstrap', 'params_alerting', 'params_alerting_delta', 'params_recovery', 'params_escapechar']
    TYPE_MAPPING_RESSOURCES_JDD_ODRE = {
        # Champs principaux
        "uid_metadata": Optional[str],
        "uid": Optional[str],
        "title": Optional[str],
        "type": Optional[str],
        "updated_at": Optional[str],
        "display_name": Optional[str],
        "enabled": Optional[str],

        # Champs datasource
        "datasource": Optional[str],
        "datasource_connection_uid": Optional[str],
        "datasource_dataset_dataset_id": Optional[str],
        "datasource_domain_domain_id": Optional[str],
        "datasource_file_uid": Optional[str],
        "datasource_headers": Optional[str],
        "datasource_permissions_user_username": Optional[str],
        "datasource_relative_url": Optional[str],
        "datasource_type": Optional[str],
        "datasource_url": Optional[str],

        # Champs params
        "params_admin_metadata": Optional[str],
        "params_alerting": Optional[str],
        "params_alerting_delta": Optional[int],
        "params_bootstrap": Optional[str],
        "params_custom_metadata": Optional[str],
        "params_dataset_stats": Optional[str],
        "params_doublequote": Optional[Union[bool, str]],
        "params_encoding": Optional[str],
        "params_escapechar": Optional[str],
        "params_extract_filename": Optional[str],
        "params_extract_geopoint": Optional[str],
        "params_extract_meta": Optional[str],
        "params_first_row_no": Optional[int],
        "params_headers_first_row": Optional[str],
        "params_interop_metadata": Optional[str],
        "params_json_object": Optional[str],
        "params_json_root": Optional[str],
        "params_private_datasets": Optional[str],
        "params_recovery": Optional[str],
        "params_separator": Optional[str],
        "params_sheet_no": Optional[str],
        "params_staged_datasets": Optional[str],

        # Champs origin
        "origin_label": Optional[str],
        "origin_type": Optional[str],

        # Champs extraction_infos
        "extraction_infos": Optional[str],
        "extraction_infos_label": Optional[str],
        "extraction_infos_type": Optional[str],

        # Autres
        "url": Optional[HttpUrl],
        "apikey": Optional[str],
        "push_url": Optional[str]

    }

    # Utile pour typer le sjon récupéré après lecture du fichier Excel (iso pour la phase de récupération des data)
    #BLOB_MONITORING_JDD_ODRE_PATH_JSON = r"src/data/blob_monitoring_JDD_ODRE.json"
    BLOB_MONITORING_JDD_ODRE_PATH_PARQUET = r"src/data/blob_monitoring_JDD_ODRE.parquet"
    LISTE_CHAMPS_BLOB_MONITORING = ['name', 'size', 'lastmodified', 'boolisdeleted', 'contenttype', 'storageaccountname', 'storagecontainername', 'fullname', 'fullname_lower', 'name_lower', 'storagecontainername_lower']
    TYPE_MAPPING_BLOB_MONITORING_JDD_ODRE = {
        "Name": Optional[str],
        "Size": Optional[int],
        "LastModified": Optional[str],
        "BoolIsDeleted": Optional[str],
        "ContentType": Optional[str],
        "StorageAcciybtBale": Optional[str],
        "StorageAccountName": Optional[str],
        "StorageContainerName": Optional[str],
        #"FullName":  Optional[HttpUrl]
        "FullName":  Optional[str]
    }


    # Regle des gestions fréquence de mise à jour [Ajustement à faire avec le métier]
    TYPE_FREQUENCE = {
        '1/4 Horaire': timedelta(minutes=15),
        '1/2 Horaire': timedelta(minutes=30),
        'Horaire': timedelta(hours=1),
        'Hebdomadaire': timedelta(days=7),
        'Journalier': timedelta(days=1),
        'Mensuel': timedelta(days=30),
        'Trimestriel': timedelta(days=90),
        'Annuel': timedelta(days=365),
        'Multiple': None,  # cas particulier
        'N/A': None,       # non applicable
    }

    REGLES_FREQUENCES = {
        # tolérances : attention = 1x fréquence, critique = 2x fréquence
        # [Ajustement à faire avec le métier]
        '1/4 Horaire': {'attention': 1.0, 'critique': 2.0},
        '1/2 Horaire': {'attention': 1.0, 'critique': 2.0},
        'Horaire': {'attention': 1.0, 'critique': 2.0},
        'Journalier': {'attention': 1.0, 'critique': 1.5},
        'Hebdomadaire': {'attention': 1.0, 'critique': 1.5},
        'Mensuel': {'attention': 1.0, 'critique': 1.5},
        'Trimestriel': {'attention': 1.0, 'critique': 1.5},
        'Annuel': {'attention': 1.0, 'critique': 1.5},
        'Multiple': {'attention': 1.0, 'critique': 1.5},
        'N/A': {'attention': 1.0, 'critique': 1.5},
    }

    SEUILS_ALERTE = {
        # Pour l'ensemble des Jdds
        'global': {  
            'ok_max_en_retard_pct': 10,      # <=10% en retard => OK
            'ko_min_critiques_pct': 20,      # >=20% critiques => KO
        },
        # les anomalies unitaires
        'jdd': {   
            'absent_last_update_is_critique': True,
            'freq_inconnue_is_attention': True,
        },
        # seuils d'interface utilisateur
        'ui': {
            'top_critiques_min': 5,      # nombre minimal de CRITIQUES dans le Top pour alerter
            'top_size_warn_min': 5       # taille minimale du Top pour avertir volumineux
        }
    }

    # Fuseau horaire de l’app (Bois-Colombes → Europe/Paris)
    TIME_ZONE = ZoneInfo("Europe/Paris")
    CACHE_SOURCES = r"src\data\cache\cache_app.json"
    # Rafraîchissement automatique des sources (09:30, lundi→vendredi)
    AUTO_REFRESH_CRON_ENABLED = True
    AUTO_REFRESH_CRON_WEEKDAYS = "mon-fri"
    AUTO_REFRESH_CRON_HOUR = 9
    AUTO_REFRESH_CRON_MINUTE = 30

    # crontab -e
    # Lundi→Vendredi à 09:30
    #30 9 * * 1-5 /chemin/vers/venv/bin/python /chemin/vers/projet/scripts/refresh_cache.py >> /var/log/tonapp/refresh_cache.log 2>&1
    #30 9 * * 1-5 C:\Users\0471IA\AppData\Local\anaconda3\envs\my_env_streamlit C:\Users\0471IA\OneDrive - NaTran\_1_Outils de supervision JDD ODRE\_7_Streamlit_app\scripts\rafraichir_cache_sources.py  >> /var/log/tonapp/refresh_cache.log 2>&1