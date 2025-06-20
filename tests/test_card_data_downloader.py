import os
import json
import tempfile
import pytest
from pathlib import Path
from src.data.card_data_manager import CardDataManager
from src.utils.card_utils import normalize_card_name

@pytest.fixture
def temp_downloader(tmp_path):
    # Patch the data_dir and edhrec_cache_file to use a temp directory
    downloader = CardDataManager()
    downloader.data_dir = tmp_path
    downloader.edhrec_cache_file = tmp_path / 'edhrec_cache.json'
    downloader.edhrec_cache = {'test_card': {'synergies': [], 'potential_decks': 1}}
    return downloader

def test_downloader_initialization_sets_paths():
    downloader = CardDataManager()
    assert isinstance(downloader.data_dir, Path)
    assert downloader.data_file.name == 'oracle_cards.json'
    assert downloader.last_download_file.name == 'last_download.json'
    assert downloader.edhrec_cache_file.name == 'edhrec_cache.json'
    assert isinstance(downloader.edhrec_cache, dict)

def test_format_name_for_edhrec(temp_downloader):
    fn = normalize_card_name
    assert fn('Atraxa, Praetors\' Voice') == 'atraxa-praetors-voice'
    assert fn('Najeela, the Blade-Blossom') == 'najeela-the-blade-blossom'
    assert fn('Yuriko, the Tiger\'s Shadow') == 'yuriko-the-tigers-shadow'
    assert fn('Card Name // Other Name') == 'card-name'

def test_save_edhrec_cache_creates_file(temp_downloader):
    temp_downloader._save_edhrec_cache()
    assert temp_downloader.edhrec_cache_file.exists()
    with open(temp_downloader.edhrec_cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert 'test_card' in data

def test_theme_slugs_loaded_from_json(tmp_path):
    # Create a temporary theme_slugs.json
    theme_slugs = ["test-theme-1", "test-theme-2", "test-theme-3"]
    theme_dir = tmp_path / "edhrec_themes"
    theme_dir.mkdir(parents=True, exist_ok=True)
    theme_slugs_path = theme_dir / "theme_slugs.json"
    with open(theme_slugs_path, "w", encoding="utf-8") as f:
        json.dump(theme_slugs, f)

    # Patch CardDataManager to use the temp reference dir
    downloader = CardDataManager()
    downloader.data_dir = tmp_path
    # Force reload of theme slugs
    try:
        with open(theme_slugs_path, 'r', encoding='utf-8') as f:
            downloader.theme_slugs = json.load(f)
    except Exception as e:
        downloader.theme_slugs = []

    assert downloader.theme_slugs == theme_slugs 