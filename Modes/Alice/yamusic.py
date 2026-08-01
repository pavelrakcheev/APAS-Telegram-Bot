import requests
import os
import json
import logging
from typing import Dict, List, Optional
from src.config import YANDEX_API_KEY

# Yandex Music API configuration
YANDEX_MUSIC_BASE_URL = "https://api.music.yandex.net"

def get_yandex_music_headers():
    """Get headers for Yandex Music API"""
    return {
        "Authorization": f"OAuth {YANDEX_API_KEY}",
        "Content-Type": "application/json"
    }

class YandexMusicAPI:
    """Класс для работы с API Яндекс Музыки"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(get_yandex_music_headers())

    def search_tracks(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск треков по запросу"""
        try:
            url = f"{YANDEX_MUSIC_BASE_URL}/search"
            params = {
                'type': 'track',
                'text': query,
                'limit': limit
            }

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            tracks = []

            if 'result' in data and 'tracks' in data['result']:
                for track in data['result']['tracks']['results']:
                    tracks.append({
                        'id': track['id'],
                        'title': track['title'],
                        'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                        'album': track['albums'][0]['title'] if track['albums'] else 'Unknown',
                        'duration': track['durationMs'],
                        'cover_url': track['coverUri'].replace('%%', '400x400') if 'coverUri' in track else None
                    })

            return tracks

        except Exception as e:
            logging.error(f"Error searching tracks: {e}")
            return []

    def get_track_info(self, track_id: str) -> Optional[Dict]:
        """Получить информацию о треке"""
        try:
            url = f"{YANDEX_MUSIC_BASE_URL}/tracks/{track_id}"

            response = self.session.get(url)
            response.raise_for_status()

            data = response.json()
            if 'result' in data:
                track = data['result'][0]
                return {
                    'id': track['id'],
                    'title': track['title'],
                    'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
                    'album': track['albums'][0]['title'] if track['albums'] else 'Unknown',
                    'duration': track['durationMs'],
                    'cover_url': track['coverUri'].replace('%%', '400x400') if 'coverUri' in track else None
                }

            return None

        except Exception as e:
            logging.error(f"Error getting track info: {e}")
            return None

    def get_my_wave(self) -> List[Dict]:
        """Получить рекомендации 'Моя волна'"""
        try:
            # Для 'Моей волны' используем feed API
            url = f"{YANDEX_MUSIC_BASE_URL}/feed"

            response = self.session.get(url)
            response.raise_for_status()

            data = response.json()

            # Ищем плейлист "Моя волна" в фиде
            if 'result' in data:
                for item in data['result']:
                    if item.get('type') == 'playlist' and 'Моя волна' in item.get('title', ''):
                        playlist_id = item['data']['id']
                        owner = item['data']['owner']['uid']

                        # Получаем треки из плейлиста
                        return self.get_playlist_tracks(owner, playlist_id)

            # Если не нашли в фиде, возвращаем популярные треки
            return self.get_popular_tracks()

        except Exception as e:
            logging.error(f"Error getting my wave: {e}")
            return self.get_popular_tracks()

    def get_playlist_tracks(self, owner_id: str, playlist_id: str) -> List[Dict]:
        """Получить треки из плейлиста"""
        try:
            url = f"{YANDEX_MUSIC_BASE_URL}/users/{owner_id}/playlists/{playlist_id}"

            response = self.session.get(url)
            response.raise_for_status()

            data = response.json()
            tracks = []

            if 'result' in data and 'tracks' in data['result']:
                for track in data['result']['tracks']:
                    if 'track' in track:
                        t = track['track']
                        tracks.append({
                            'id': t['id'],
                            'title': t['title'],
                            'artist': t['artists'][0]['name'] if t['artists'] else 'Unknown',
                            'album': t['albums'][0]['title'] if t['albums'] else 'Unknown',
                            'duration': t['durationMs'],
                            'cover_url': t['coverUri'].replace('%%', '400x400') if 'coverUri' in t else None
                        })

            return tracks[:10]  # Ограничиваем до 10 треков

        except Exception as e:
            logging.error(f"Error getting playlist tracks: {e}")
            return []

    def get_popular_tracks(self) -> List[Dict]:
        """Получить популярные треки (запасной вариант)"""
        try:
            # Ищем популярные треки
            return self.search_tracks("популярные песни", 10)
        except Exception as e:
            logging.error(f"Error getting popular tracks: {e}")
            return []

# Глобальный экземпляр API
yandex_music_api = YandexMusicAPI()

def format_track_info(track: Dict) -> str:
    """Форматировать информацию о треке"""
    duration_min = track['duration'] // 60000
    duration_sec = (track['duration'] % 60000) // 1000

    return f"""🎵 **{track['title']}**
👤 Исполнитель: {track['artist']}
💿 Альбом: {track['album']}
⏱️ Длительность: {duration_min}:{duration_sec:02d}"""

def format_tracks_list(tracks: List[Dict]) -> str:
    """Форматировать список треков"""
    if not tracks:
        return "К сожалению, ничего не найдено."

    result = "🎶 **Найденные треки:**\n\n"
    for i, track in enumerate(tracks[:10], 1):
        duration_min = track['duration'] // 60000
        duration_sec = (track['duration'] % 60000) // 1000
        result += f"{i}. **{track['title']}** - {track['artist']} ({duration_min}:{duration_sec:02d})\n"

    return result

async def process_music_command(query: str) -> str:
    """Обработать музыкальную команду Алисы"""
    query_lower = query.lower().strip()

    # Обработка команды "включи мою волну"
    if "мою волну" in query_lower or "моя волна" in query_lower:
        tracks = yandex_music_api.get_my_wave()
        if tracks:
            response = "🎵 **Включаю вашу волну!**\n\n"
            response += "Сейчас играет:\n"
            response += format_track_info(tracks[0])
            if len(tracks) > 1:
                response += f"\n\nДалее в плейлисте: {len(tracks)-1} треков"
            return response
        else:
            return "🎵 К сожалению, не удалось загрузить вашу волну. Попробуйте поискать музыку по названию."

    # Обработка поиска музыки
    elif any(word in query_lower for word in ["включи", "найди", "поищи", "играй"]):
        # Извлекаем название трека/артиста из запроса
        search_query = query_lower
        for prefix in ["включи", "найди", "поищи", "играй"]:
            if search_query.startswith(prefix):
                search_query = search_query[len(prefix):].strip()
                break

        if search_query:
            tracks = yandex_music_api.search_tracks(search_query)
            if tracks:
                response = f"🎵 **Результаты поиска по запросу '{search_query}':**\n\n"
                response += format_track_info(tracks[0])
                if len(tracks) > 1:
                    response += f"\n\nНайдено еще {len(tracks)-1} треков"
                return response
            else:
                return f"🎵 К сожалению, ничего не найдено по запросу '{search_query}'."
        else:
            return "🎵 Пожалуйста, уточните, какую музыку вы хотите найти."

    # Обработка других музыкальных команд
    elif "что играет" in query_lower or "текущий трек" in query_lower:
        return "🎵 Сейчас я не воспроизвожу музыку. Скажите 'включи мою волну' или назовите трек/артиста!"

    elif "останови" in query_lower or "стоп" in query_lower:
        return "🎵 Музыка остановлена."

    else:
        return "🎵 Я могу помочь с музыкой! Попробуйте:\n• 'включи мою волну'\n• 'найди название трека'\n• 'включи артиста"