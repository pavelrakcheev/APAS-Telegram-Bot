import os
import logging
import json
from typing import Dict, List, Optional, Tuple

from yandex_music import Client
from yandex_music.exceptions import YandexMusicError
from src.config import YANDEX_API_KEY, YANDEX_MUSIC_ADMIN_TOKEN

class YandexMusicAPI:
    """Класс для работы с API Яндекс Музыки через официальную библиотеку"""

    USER_TOKENS_FILE = "data/yandex_music_tokens.json"

    # Специальный токен для администратора
    ADMIN_USER_ID = "349746155"
    ADMIN_TOKEN = YANDEX_MUSIC_ADMIN_TOKEN

    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id
        self.client = None
        self._init_client()

    def _init_client(self):
        """Инициализация клиента Yandex Music"""
        try:
            # Проверяем, есть ли токен для пользователя
            user_tokens = self._load_user_tokens()
            user_token = user_tokens.get(self.user_id, '') if self.user_id else ''

            # Специальная проверка для администратора
            if self.user_id == self.ADMIN_USER_ID:
                user_token = self.ADMIN_TOKEN

            if user_token:
                # Используем персональный токен пользователя
                self.client = Client(user_token).init()
            else:
                # Анонимный клиент для поиска (без токена)
                self.client = Client().init()
        except Exception as e:
            logging.error(f"Error initializing Yandex Music client: {e}")
            # Попытка создать анонимный клиент
            try:
                self.client = Client().init()
            except Exception as e2:
                logging.error(f"Error creating anonymous client: {e2}")
                self.client = None

    def _load_user_tokens(self) -> Dict[str, str]:
        """Загрузить токены пользователей"""
        try:
            if os.path.exists(self.USER_TOKENS_FILE):
                with open(self.USER_TOKENS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading user tokens: {e}")
        return {}

    def _save_user_tokens(self, tokens: Dict[str, str]):
        """Сохранить токены пользователей"""
        try:
            with open(self.USER_TOKENS_FILE, 'w', encoding='utf-8') as f:
                json.dump(tokens, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving user tokens: {e}")

    def has_personal_access(self) -> bool:
        """Проверяет, есть ли персональный доступ у пользователя"""
        if not self.user_id:
            return False
        # Администратор всегда имеет доступ
        if self.user_id == self.ADMIN_USER_ID:
            return True
        user_tokens = self._load_user_tokens()
        return self.user_id in user_tokens and bool(user_tokens[self.user_id])

    def set_user_token(self, token: str):
        """Установить токен для пользователя"""
        if self.user_id:
            user_tokens = self._load_user_tokens()
            user_tokens[self.user_id] = token
            self._save_user_tokens(user_tokens)
            # Переинициализируем клиент с новым токеном
            self._init_client()

    def search_tracks(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск треков по запросу"""
        if not self.client:
            return []

        try:
            search_result = self.client.search(query, type_='track')
            tracks = []
            if search_result and search_result.tracks:
                for track in search_result.tracks.results[:limit]:
                    tracks.append({
                        'id': track.id,
                        'title': track.title,
                        'artist': track.artists[0].name if track.artists else 'Unknown',
                        'album': track.albums[0].title if track.albums else 'Unknown',
                        'duration': track.duration_ms,
                        'cover_url': track.cover_uri.replace('%%', '400x400') if track.cover_uri else None,
                        'track_obj': track  # Сохраняем объект для дополнительных операций
                    })
            return tracks
        except YandexMusicError as e:
            logging.error(f"Yandex Music API error in search_tracks: {e}")
            # Возвращаем тестовые данные для демонстрации
            return self._get_test_tracks(query, limit)
        except Exception as e:
            logging.error(f"Error searching tracks: {e}")
            # Возвращаем тестовые данные для демонстрации
            return self._get_test_tracks(query, limit)

    def _get_test_tracks(self, query: str, limit: int = 10) -> List[Dict]:
        """Возвращает тестовые данные для демонстрации"""
        test_tracks = [
            {
                'id': '1',
                'title': f'Тестовый трек для "{query}"',
                'artist': 'Тестовый исполнитель',
                'album': 'Тестовый альбом',
                'duration': 180000,  # 3 минуты
                'cover_url': None,
                'track_obj': None
            },
            {
                'id': '2',
                'title': f'Ещё один трек для "{query}"',
                'artist': 'Другой исполнитель',
                'album': 'Другой альбом',
                'duration': 240000,  # 4 минуты
                'cover_url': None,
                'track_obj': None
            }
        ]
        return test_tracks[:limit]

    def get_track_info(self, track_id: str) -> Optional[Dict]:
        """Получить информацию о треке"""
        if not self.client:
            return None

        try:
            track = self.client.tracks(track_id)[0]
            return {
                'id': track.id,
                'title': track.title,
                'artist': track.artists[0].name if track.artists else 'Unknown',
                'album': track.albums[0].title if track.albums else 'Unknown',
                'duration': track.duration_ms,
                'cover_url': track.cover_uri.replace('%%', '400x400') if track.cover_uri else None,
                'track_obj': track
            }
        except Exception as e:
            logging.error(f"Error getting track info: {e}")
            return None

    def get_my_wave(self) -> List[Dict]:
        """Получить рекомендации 'Моя волна'"""
        if not self.client:
            return []

        try:
            # Получаем персональные станции
            stations = self.client.rotor_stations_dashboard()

            # Ищем станцию "Моя волна"
            my_wave_station = None
            if stations:
                for station in stations:
                    if hasattr(station, 'station') and station.station.name:
                        if 'моя волна' in station.station.name.lower():
                            my_wave_station = station.station
                            break

            if my_wave_station:
                # Получаем треки из станции
                rotor_tracks = self.client.rotor_station_tracks(my_wave_station.id)
                tracks = []
                if rotor_tracks and hasattr(rotor_tracks, 'sequence'):
                    for rotor_track in rotor_tracks.sequence[:10]:
                        track = rotor_track.track
                        tracks.append({
                            'id': track.id,
                            'title': track.title,
                            'artist': track.artists[0].name if track.artists else 'Unknown',
                            'album': track.albums[0].title if track.albums else 'Unknown',
                            'duration': track.duration_ms,
                            'cover_url': track.cover_uri.replace('%%', '400x400') if track.cover_uri else None,
                            'track_obj': track
                        })
                return tracks
            else:
                # Если не нашли "Мою волну", возвращаем популярные треки
                return self.get_popular_tracks()
        except Exception as e:
            logging.error(f"Error getting my wave: {e}")
            return self.get_popular_tracks()

    def get_popular_tracks(self) -> List[Dict]:
        """Получить популярные треки"""
        try:
            # Ищем популярные плейлисты или чарты
            charts = self.client.chart()
            tracks = []
            if charts and hasattr(charts, 'tracks'):
                for chart_track in charts.tracks[:10]:
                    track = chart_track.track
                    tracks.append({
                        'id': track.id,
                        'title': track.title,
                        'artist': track.artists[0].name if track.artists else 'Unknown',
                        'album': track.albums[0].title if track.albums else 'Unknown',
                        'duration': track.duration_ms,
                        'cover_url': track.cover_uri.replace('%%', '400x400') if track.cover_uri else None,
                        'track_obj': track
                    })
            elif charts and hasattr(charts, 'chart') and hasattr(charts.chart, 'tracks'):
                for chart_track in charts.chart.tracks[:10]:
                    track = chart_track.track
                    tracks.append({
                        'id': track.id,
                        'title': track.title,
                        'artist': track.artists[0].name if track.artists else 'Unknown',
                        'album': track.albums[0].title if track.albums else 'Unknown',
                        'duration': track.duration_ms,
                        'cover_url': track.cover_uri.replace('%%', '400x400') if track.cover_uri else None,
                        'track_obj': track
                    })
            return tracks
        except Exception as e:
            logging.error(f"Error getting popular tracks: {e}")
            # Возвращаем тестовые популярные треки
            return self._get_test_popular_tracks()

    def _get_test_popular_tracks(self) -> List[Dict]:
        """Возвращает тестовые популярные треки"""
        return [
            {
                'id': '1001',
                'title': 'Популярный трек 1',
                'artist': 'Популярный исполнитель 1',
                'album': 'Хиты 2024',
                'duration': 210000,
                'cover_url': None,
                'track_obj': None
            },
            {
                'id': '1002',
                'title': 'Популярный трек 2',
                'artist': 'Популярный исполнитель 2',
                'album': 'Топ чарты',
                'duration': 195000,
                'cover_url': None,
                'track_obj': None
            },
            {
                'id': '1003',
                'title': 'Популярный трек 3',
                'artist': 'Популярный исполнитель 3',
                'album': 'Лучшее',
                'duration': 225000,
                'cover_url': None,
                'track_obj': None
            }
        ]

    def get_user_playlists(self) -> List[Dict]:
        """Получить плейлисты пользователя (требует авторизации)"""
        if not self.client:
            return []

        try:
            playlists = self.client.users_playlists_list()
            result = []
            for playlist in playlists:
                result.append({
                    'id': playlist.playlist_id,
                    'title': playlist.title,
                    'description': playlist.description,
                    'track_count': playlist.track_count,
                    'owner': playlist.owner.name if playlist.owner else 'Unknown'
                })
            return result
        except Exception as e:
            logging.error(f"Error getting user playlists: {e}")
            return []

    def get_playlist_tracks(self, user_id: str, playlist_id: str) -> List[Dict]:
        """Получить треки из плейлиста"""
        if not self.client:
            return []

        try:
            playlist = self.client.users_playlists(playlist_id, user_id)
            tracks = []
            for playlist_track in playlist.tracks[:10]:
                track = playlist_track.track
                tracks.append({
                    'id': track.id,
                    'title': track.title,
                    'artist': track.artists[0].name if track.artists else 'Unknown',
                    'album': track.albums[0].title if track.albums else 'Unknown',
                    'duration': track.duration_ms,
                    'cover_url': track.cover_uri.replace('%%', '400x400') if track.cover_uri else None,
                    'track_obj': track
                })
            return tracks
        except Exception as e:
            logging.error(f"Error getting playlist tracks: {e}")
            return []
    def get_recently_added_tracks(self) -> List[Dict]:
        """Получить недавно добавленные треки пользователя"""
        if not self.client:
            return []

        try:
            # Получаем лайкнутые треки пользователя (они же добавленные)
            likes = self.client.users_likes_tracks()
            tracks = []
            if likes and hasattr(likes, 'tracks'):
                # Сортируем по дате добавления (последние сначала)
                sorted_tracks = sorted(likes.tracks, key=lambda x: x.timestamp, reverse=True)
                for like_track in sorted_tracks[:10]:
                    track = like_track.track
                    tracks.append({
                        'id': track.id,
                        'title': track.title,
                        'artist': track.artists[0].name if track.artists else 'Unknown',
                        'album': track.albums[0].title if track.albums else 'Unknown',
                        'duration': track.duration_ms,
                        'cover_url': track.cover_uri.replace('%%', '400x400') if track.cover_uri else None,
                        'track_obj': track,
                        'added_at': like_track.timestamp
                    })
            return tracks
        except Exception as e:
            logging.error(f"Error getting recently added tracks: {e}")
            return []


def get_yandex_music_api(user_id: Optional[str] = None) -> YandexMusicAPI:
    """Получить экземпляр API для пользователя"""
    return YandexMusicAPI(user_id)


# Глобальный экземпляр API для анонимного доступа
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


async def process_music_command(query: str, user_id: Optional[str] = None) -> str:
    """Обработать музыкальную команду Алисы"""
    # Получаем API для конкретного пользователя
    api = get_yandex_music_api(user_id)

    query_lower = query.lower().strip()

    # Обработка команды "включи мою волну"
    if "мою волну" in query_lower or "моя волна" in query_lower:
        tracks = api.get_my_wave()
        if tracks:
            # Проверяем, являются ли треки популярными (fallback)
            is_personal = api.has_personal_access() and len(tracks) > 0 and 'track_obj' in tracks[0]
            if is_personal:
                response = "🎵 **Включаю вашу волну!**\n\n"
                response += "Сейчас играет:\n"
                response += format_track_info(tracks[0])
                if len(tracks) > 1:
                    response += f"\n\nДалее в плейлисте: {len(tracks)-1} треков"
                return response
            else:
                response = "🎵 **Популярные треки на Яндекс Музыке**\n\n"
                response += "Сейчас играет:\n"
                response += format_track_info(tracks[0])
                if len(tracks) > 1:
                    response += f"\n\nДалее в плейлисте: {len(tracks)-1} треков"
                response += "\n\n*Персональные станции недоступны. Подключите аккаунт Яндекс Музыки для личных рекомендаций.*"
                return response
        else:
            return "🎵 К сожалению, не удалось загрузить музыку. Попробуйте поискать музыку по названию."

    # Обработка запроса о последней добавленной песне
    if any(phrase in query_lower for phrase in ["последнюю песню", "последняя песня", "последний трек", "последнюю добавил", "добавил последнюю"]):
        tracks = api.get_recently_added_tracks()
        if tracks:
            response = "🎵 **Ваша последняя добавленная песня:**\n\n"
            response += format_track_info(tracks[0])
            if len(tracks) > 1:
                response += f"\n\nРанее добавленные: {len(tracks)-1} треков"
            return response
        else:
            return "🎵 Не удалось получить информацию о добавленных песнях. Возможно, у вас нет лайкнутых треков или требуется авторизация."

    # Обработка поиска музыки
    elif any(word in query_lower for word in ["включи", "найди", "поищи", "играй"]):
        # Извлекаем название трека/артиста из запроса
        search_query = query_lower
        for prefix in ["включи", "найди", "поищи", "играй"]:
            if search_query.startswith(prefix):
                search_query = search_query[len(prefix):].strip()
                break

        if search_query:
            tracks = api.search_tracks(search_query)
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
        has_access = api.has_personal_access()
        access_status = "✅ Персонализированный доступ активен" if has_access else "❌ Доступ ограничен (анонимный режим)"

        return f"""🎵 Я могу помочь с музыкой! Вот что я умею:

• **Включи мою волну** — персональные рекомендации
• **Найди [трек/артист]** — поиск музыки
• **Включи [артист]** — музыка исполнителя
• **Какая последняя песня я добавил** — информация о недавно добавленных треках

{access_status}

Для персонализированных рекомендаций подключите аккаунт Яндекс Музыки через /yamusic"""