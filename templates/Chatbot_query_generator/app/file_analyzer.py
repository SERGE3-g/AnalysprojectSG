import os
#import magic
import hashlib
import logging
from typing import Dict, List, Optional, Union, Tuple, Any
from pathlib import Path
import pandas as pd
import docx
import PyPDF2
from PIL import Image
import json
import xml.etree.ElementTree as ET
import csv
import sqlite3
import zipfile
import yaml
import mimetypes
from datetime import datetime
import chardet
import shutil
import numpy as np
from collections import Counter
import re
import struct
import exifread
from moviepy import VideoFileClip
from pandas.io.formats import string
from pdf2image import convert_from_path
import pytesseract
#import cv2
import matplotlib.pyplot as plt
#from moviepy.editor import VideoFileClip
import soundfile as sf
from pydub import AudioSegment
import tabula


class FileAnalyzer:
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Inizializza l'analizzatore di file

        Args:
            cache_dir: Directory per la cache (opzionale)
        """
        self.logger = logging.getLogger(__name__)
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), '.file_analyzer_cache')
        os.makedirs(self.cache_dir, exist_ok=True)

        self.supported_formats = {
            'text': ['.txt', '.csv', '.json', '.xml', '.yaml', '.yml', '.ini', '.log', '.md', '.rst', '.sql'],
            'document': ['.doc', '.docx', '.pdf', '.rtf', '.odt', '.epub', '.mobi'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'],
            'database': ['.db', '.sqlite', '.sqlite3', '.mdb', '.accdb'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            'audio': ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.wma'],
            'video': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
            'executable': ['.exe', '.dll', '.so', '.dylib'],
            'code': ['.py', '.js', '.java', '.cpp', '.h', '.cs', '.php', '.rb']
        }

        # Cache per le informazioni dei file
        self.cache = {}

    def analyze_file(self, file_path: Union[str, Path]) -> Dict:
        """Analizza un file e restituisce informazioni dettagliate"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File non trovato: {file_path}")

            # Controlla la cache
            cache_key = f"{file_path}_{os.path.getmtime(file_path)}"
            if cache_key in self.cache:
                return self.cache[cache_key]

            basic_info = self._get_basic_info(file_path)
            file_type = self._detect_file_type(file_path)
            basic_info['detected_type'] = file_type

            # Analisi specifica per tipo
            analysis_methods = {
                'text': self._analyze_text_file,
                'document': self._analyze_document,
                'image': self._analyze_image,
                'database': self._analyze_database,
                'archive': self._analyze_archive,
                'audio': self._analyze_audio,
                'video': self._analyze_video,
                'executable': self._analyze_executable,
                'code': self._analyze_code_file
            }

            content_info = {}
            if file_type in analysis_methods:
                content_info = analysis_methods[file_type](file_path)

            result = {**basic_info, 'content_analysis': content_info}
            self.cache[cache_key] = result
            return result

        except Exception as e:
            self.logger.error(f"Errore nell'analisi del file {file_path}: {str(e)}")
            raise

    def convert_file(self, input_path: Path, output_format: str) -> Path:
        """
        Converte un file in un altro formato

        Args:
            input_path: Percorso del file di input
            output_format: Formato di destinazione (es. 'pdf', 'png')

        Returns:
            Path: Percorso del file convertito
        """
        try:
            input_ext = input_path.suffix.lower()
            output_path = input_path.with_suffix(f".{output_format}")

            # Gestione conversioni documenti
            if input_ext in ['.docx', '.doc'] and output_format == 'pdf':
                return self._convert_doc_to_pdf(input_path, output_path)

            # Gestione conversioni immagini
            elif input_ext in self.supported_formats['image'] and output_format in ['jpg', 'png', 'pdf']:
                return self._convert_image(input_path, output_path)

            # Gestione conversioni audio
            elif input_ext in self.supported_formats['audio'] and output_format in ['mp3', 'wav']:
                return self._convert_audio(input_path, output_path)

            else:
                raise ValueError(f"Conversione da {input_ext} a {output_format} non supportata")

        except Exception as e:
            self.logger.error(f"Errore nella conversione del file: {str(e)}")
            raise

    def extract_text(self, file_path: Path) -> str:
        """
        Estrae il testo da vari tipi di file

        Args:
            file_path: Percorso del file

        Returns:
            str: Testo estratto
        """
        try:
            file_type = self._detect_file_type(file_path)

            if file_type == 'document':
                if file_path.suffix.lower() == '.pdf':
                    return self._extract_text_from_pdf(file_path)
                elif file_path.suffix.lower() == '.docx':
                    return self._extract_text_from_docx(file_path)

            elif file_type == 'image':
                return self._extract_text_from_image(file_path)

            elif file_type == 'text':
                return self._read_text_file(file_path)

            else:
                raise ValueError(f"Estrazione testo non supportata per {file_path.suffix}")

        except Exception as e:
            self.logger.error(f"Errore nell'estrazione del testo: {str(e)}")
            raise

    def _analyze_image(self, file_path: Path) -> Dict:
        """Analizza immagini"""
        try:
            with Image.open(file_path) as img:
                # Informazioni base
                info = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'aspect_ratio': round(img.width / img.height, 2),
                    'num_frames': getattr(img, 'n_frames', 1),
                    'is_animated': getattr(img, 'is_animated', False)
                }

                # Analisi dei colori
                if img.mode == 'RGB':
                    img_array = np.array(img)
                    info['color_analysis'] = {
                        'mean_rgb': img_array.mean(axis=(0, 1)).tolist(),
                        'std_rgb': img_array.std(axis=(0, 1)).tolist(),
                        'dominant_colors': self._get_dominant_colors(img)
                    }

                # Metadati EXIF
                if hasattr(img, '_getexif') and img._getexif():
                    with open(file_path, 'rb') as f:
                        exif = exifread.process_file(f)
                        info['exif'] = {str(k): str(v) for k, v in exif.items()}

                # Analisi qualità
                info['quality_analysis'] = {
                    'entropy': self._calculate_image_entropy(img),
                    'blur_detection': self._detect_blur(np.array(img)),
                    'compression_ratio': os.path.getsize(file_path) / (img.width * img.height)
                }

                return info

        except Exception as e:
            self.logger.error(f"Errore nell'analisi dell'immagine: {str(e)}")
            raise

    def _analyze_audio(self, file_path: Path) -> Dict:
        """Analizza file audio"""
        try:
            audio = AudioSegment.from_file(str(file_path))

            # Carica il file per analisi dettagliate
            data, samplerate = sf.read(str(file_path))

            return {
                'format': file_path.suffix[1:],
                'duration': len(audio) / 1000.0,  # secondi
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'frame_rate': audio.frame_rate,
                'frame_count': len(data),
                'bitrate': audio.frame_rate * audio.sample_width * 8 * audio.channels,
                'max_amplitude': float(np.abs(data).max()),
                'rms_energy': float(np.sqrt(np.mean(data ** 2))),
                'spectrum_analysis': self._analyze_audio_spectrum(data, samplerate)
            }
        except Exception as e:
            self.logger.error(f"Errore nell'analisi audio: {str(e)}")
            raise

    def _analyze_video(self, file_path: Path) -> Dict:
        """Analizza file video"""
        try:
            video = VideoFileClip(str(file_path))

            # Estrai un frame per l'anteprima
            thumbnail_path = os.path.join(self.cache_dir, f"{file_path.stem}_thumb.jpg")
            video.save_frame(thumbnail_path, t=1.0)

            return {
                'format': file_path.suffix[1:],
                'duration': video.duration,
                'size': video.size,
                'fps': video.fps,
                'audio_present': video.audio is not None,
                'rotation': video.rotation if hasattr(video, 'rotation') else 0,
                'bitrate': os.path.getsize(file_path) * 8 / video.duration,
                'thumbnail_path': thumbnail_path,
                'frame_analysis': self._analyze_video_frames(video)
            }
        except Exception as e:
            self.logger.error(f"Errore nell'analisi video: {str(e)}")
            raise
        finally:
            if 'video' in locals():
                video.close()

    def _analyze_database(self, file_path: Path) -> Dict:
        """Analizza file database"""
        try:
            conn = sqlite3.connect(str(file_path))
            cursor = conn.cursor()

            # Ottieni informazioni sulle tabelle
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            database_info = {
                'format': 'SQLite',
                'tables': {},
                'size': os.path.getsize(file_path),
                'version': sqlite3.sqlite_version
            }

            for table in tables:
                table_name = table[0]
                # Schema della tabella
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()

                # Statistiche della tabella
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                row_count = cursor.fetchone()[0]

                database_info['tables'][table_name] = {
                    'columns': [{'name': col[1], 'type': col[2]} for col in columns],
                    'row_count': row_count
                }

                # Aggiungi sample data se la tabella non è vuota
                if row_count > 0:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                    sample_data = cursor.fetchall()
                    database_info['tables'][table_name]['sample_data'] = sample_data

            return database_info

        except Exception as e:
            self.logger.error(f"Errore nell'analisi del database: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()

    def _analyze_executable(self, file_path: Path) -> Dict:
        """Analizza file eseguibili"""
        try:
            with open(file_path, 'rb') as f:
                # Leggi l'header del file
                header = f.read(2)

                # Analisi base
                info = {
                    'format': 'Executable',
                    'size': os.path.getsize(file_path),
                    'permissions': oct(os.stat(file_path).st_mode)[-3:],
                    'is_64bit': self._check_if_64bit(file_path)
                }

                # Identifica il tipo di eseguibile
                if header.startswith(b'MZ'):  # Windows PE
                    info.update(self._analyze_pe(file_path))
                elif header.startswith(b'\x7fELF'):  # Linux ELF
                    info.update(self._analyze_elf(file_path))
                elif header.startswith(b'\xCA\xFE'):  # macOS Mach-O
                    info.update(self._analyze_macho(file_path))

                # Analisi delle stringhe
                info['strings_analysis'] = self._analyze_binary_strings(file_path)

                return info

        except Exception as e:
            self.logger.error(f"Errore nell'analisi dell'eseguibile: {str(e)}")
            raise

    def _analyze_code_file(self, file_path: Path) -> Dict:
        """Analizza file di codice sorgente"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Analisi base del codice
            lines = content.splitlines()

            # Cerca import e dipendenze
            imports = re.findall(r'import\s+[\w\s,]+|from\s+[\w.]+\s+import\s+[\w\s,]+', content)

            # Cerca definizioni di funzioni e classi
            functions = re.findall(r'def\s+(\w+)\s*\(', content)
            classes = re.findall(r'class\s+(\w+)[\s:\(]', content)

            # Cerca commenti e docstrings
            comments = []
            docstrings = []
            in_docstring = False
            docstring_buffer = []

            for line in lines:
                # Trova commenti inline
                if '#' in line:
                    comment_start = line.find('#')
                    if not re.search(r'[\'"][^\']*#[^\']*[\'"]', line[:comment_start]):
                        comments.append(line[comment_start:].strip())

                # Trova docstrings
                if '"""' in line or "'''" in line:
                    if not in_docstring:
                        in_docstring = True
                        docstring_buffer = [line]
                    else:
                        in_docstring = False
                        docstring_buffer.append(line)
                        docstrings.append('\n'.join(docstring_buffer))
                elif in_docstring:
                    docstring_buffer.append(line)

            # Analisi di complessità
            complexity = {
                'cyclomatic': self._calculate_cyclomatic_complexity(content),
                'nesting_depth': self._calculate_max_nesting(lines),
                'avg_function_length': self._calculate_avg_function_length(lines)
            }

            # Cerca TODO e FIXME
            todos = re.findall(r'#\s*(?:TODO|FIXME)\s*:?\s*(.*)', content, re.IGNORECASE)

            # Analisi del codice
            code_analysis = {
                'total_lines': len(lines),
                'blank_lines': len([l for l in lines if not l.strip()]),
                'comment_lines': len(comments),
                'code_lines': len(lines) - len([l for l in lines if not l.strip()]) - len(comments),
                'avg_line_length': sum(len(l) for l in lines) / len(lines) if lines else 0,
                'imports': imports,
                'functions': {
                    'count': len(functions),
                    'names': functions
                },
                'classes': {
                    'count': len(classes),
                    'names': classes
                },
                'docstrings': docstrings,
                'comments': comments,
                'todos': todos,
                'complexity_metrics': complexity
            }

            # Statistiche aggiuntive
            code_analysis['statistics'] = {
                'lines_per_function': code_analysis['code_lines'] / len(functions) if functions else 0,
                'comment_ratio': len(comments) / len(lines) if lines else 0,
                'docstring_ratio': len(docstrings) / (len(functions) + len(classes)) if (functions or classes) else 0
            }

            return code_analysis

        except Exception as e:
            self.logger.error(f"Errore nell'analisi del file di codice: {str(e)}")
            raise

    def _calculate_cyclomatic_complexity(self, content: str) -> int:
        """Calcola la complessità ciclomatica del codice"""
        decision_points = len(re.findall(r'\b(if|while|for|and|or)\b', content))
        return decision_points + 1

    def _calculate_max_nesting(self, lines: List[str]) -> int:
        """Calcola la profondità massima di nesting"""
        max_depth = current_depth = 0
        for line in lines:
            indentation = len(line) - len(line.lstrip())
            current_depth = indentation // 4  # Assume 4 spazi per livello
            max_depth = max(max_depth, current_depth)
        return max_depth

    def _calculate_avg_function_length(self, lines: List[str]) -> float:
        """Calcola la lunghezza media delle funzioni"""
        function_lengths = []
        current_function_lines = 0
        in_function = False

        for line in lines:
            if re.match(r'\s*def\s+', line):
                if in_function:
                    function_lengths.append(current_function_lines)
                in_function = True
                current_function_lines = 1
            elif in_function:
                if line.strip():
                    current_function_lines += 1
                if not line.strip() and current_function_lines > 0:
                    function_lengths.append(current_function_lines)
                    in_function = False
                    current_function_lines = 0

        # Aggiungi l'ultima funzione se presente
        if current_function_lines > 0:
            function_lengths.append(current_function_lines)

        return sum(function_lengths) / len(function_lengths) if function_lengths else 0

    def _analyze_binary_strings(self, file_path: Path) -> Dict:
        """
        Analizza le stringhe contenute in un file binario

        Args:
            file_path: Percorso del file da analizzare

        Returns:
            Dict: Dizionario contenente l'analisi delle stringhe
        """
        try:
            # Pattern per diversi tipi di stringhe
            patterns = {
                'urls': rb'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
                'emails': rb'[\w\.-]+@[\w\.-]+\.\w+',
                'ipv4': rb'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                'paths': rb'(?:/[\w\.-]+)+|(?:[A-Za-z]:\\[\w\.-]+(?:\\[\w\.-]+)*)',
                'commands': rb'(?:sudo|chmod|chown|mv|cp|rm|cat|echo|bash|cmd\.exe|powershell\.exe)[^\n]*',
                'api_keys': rb'(?:api[_-]?key|api[_-]?token|auth[_-]?token)[^\n]*',
                'passwords': rb'(?:password|passwd|pwd)[^\n]*'
            }

            with open(file_path, 'rb') as f:
                data = f.read()

            # Analisi base delle stringhe
            basic_strings = re.findall(b'[ -~]{4,}', data)
            decoded_strings = [s.decode('utf-8', errors='ignore') for s in basic_strings]

            # Analisi avanzata
            result = {
                'statistics': {
                    'total_strings': len(decoded_strings),
                    'total_bytes': sum(len(s) for s in basic_strings),
                    'avg_length': sum(len(s) for s in basic_strings) / len(basic_strings) if basic_strings else 0,
                    'unique_strings': len(set(decoded_strings))
                },
                'categorized_strings': {},
                'potential_sensitive': [],
                'frequent_patterns': [],
                'encoding_analysis': self._analyze_string_encodings(basic_strings),
                'strings_by_length': {
                    'short': [s for s in decoded_strings if len(s) < 10],
                    'medium': [s for s in decoded_strings if 10 <= len(s) < 50],
                    'long': [s for s in decoded_strings if len(s) >= 50]
                }
            }

            # Categorizza le stringhe trovate
            for category, pattern in patterns.items():
                matches = re.findall(pattern, data)
                result['categorized_strings'][category] = [
                    m.decode('utf-8', errors='ignore') for m in matches
                ]

            # Identifica potenziali informazioni sensibili
            sensitive_patterns = {
                'api_key': rb'[a-zA-Z0-9]{32,}',
                'private_key': rb'-----BEGIN (?:RSA )?PRIVATE KEY-----[^-]+-----END (?:RSA )?PRIVATE KEY-----',
                'cert': rb'-----BEGIN CERTIFICATE-----[^-]+-----END CERTIFICATE-----',
                'aws_key': rb'AKIA[0-9A-Z]{16}',
                'jwt': rb'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'
            }

            for key, pattern in sensitive_patterns.items():
                matches = re.findall(pattern, data)
                if matches:
                    result['potential_sensitive'].extend({
                                                             'type': key,
                                                             'value': m.decode('utf-8', errors='ignore')[:20] + '...'
                                                             # Troncato per sicurezza
                                                         } for m in matches)

            # Analizza pattern frequenti
            if decoded_strings:
                result['frequent_patterns'] = self._analyze_string_patterns(decoded_strings)

            # Aggiunge analisi caratteri
            result['character_analysis'] = self._analyze_string_characters(decoded_strings)

            return result

        except Exception as e:
            self.logger.error(f"Errore nell'analisi delle stringhe binarie: {str(e)}")
            return {
                'error': str(e),
                'statistics': {'total_strings': 0},
                'categorized_strings': {},
                'potential_sensitive': [],
                'frequent_patterns': []
            }

    def _analyze_string_encodings(self, binary_strings: List[bytes]) -> Dict:
        """Analizza le possibili codifiche delle stringhe"""
        encodings = ['utf-8', 'ascii', 'utf-16', 'utf-32', 'iso-8859-1', 'cp1252']
        results = {}

        for encoding in encodings:
            valid_strings = 0
            for binary in binary_strings:
                try:
                    binary.decode(encoding)
                    valid_strings += 1
                except UnicodeDecodeError:
                    continue

            results[encoding] = {
                'valid_strings': valid_strings,
                'percentage': (valid_strings / len(binary_strings) * 100) if binary_strings else 0
            }

        return results

    def _analyze_string_patterns(self, strings: List[str]) -> List[Dict]:
        """Analizza pattern comuni nelle stringhe"""
        patterns = []

        # Trova pattern di formattazione comuni
        format_patterns = {
            'uuid': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            'date': r'\d{4}-\d{2}-\d{2}',
            'time': r'\d{2}:\d{2}:\d{2}',
            'version': r'\d+\.\d+\.\d+',
            'hex': r'0x[0-9a-fA-F]+',
            'json': r'\{.*\}',
            'xml': r'<[^>]+>'
        }

        for pattern_name, pattern in format_patterns.items():
            matches = sum(1 for s in strings if re.search(pattern, s))
            if matches > 0:
                patterns.append({
                    'pattern': pattern_name,
                    'count': matches,
                    'percentage': (matches / len(strings) * 100)
                })

        # Identifica prefissi/suffissi comuni
        common_prefixes = []
        common_suffixes = []

        for length in range(2, 6):
            prefixes = Counter(s[:length] for s in strings if len(s) >= length)
            suffixes = Counter(s[-length:] for s in strings if len(s) >= length)

            for prefix, count in prefixes.most_common(3):
                if count >= len(strings) * 0.1:  # Almeno 10% delle stringhe
                    common_prefixes.append({
                        'value': prefix,
                        'count': count,
                        'percentage': (count / len(strings) * 100)
                    })

            for suffix, count in suffixes.most_common(3):
                if count >= len(strings) * 0.1:
                    common_suffixes.append({
                        'value': suffix,
                        'count': count,
                        'percentage': (count / len(strings) * 100)
                    })

        patterns.extend([
            {'type': 'common_prefixes', 'patterns': common_prefixes},
            {'type': 'common_suffixes', 'patterns': common_suffixes}
        ])

        return patterns

    def _analyze_string_characters(self, strings: List[str]) -> Dict:
        """Analizza la distribuzione dei caratteri nelle stringhe"""
        all_chars = ''.join(strings)
        char_count = Counter(all_chars)

        return {
            'total_chars': len(all_chars),
            'unique_chars': len(char_count),
            'char_distribution': {
                'alphabetic': sum(1 for c in all_chars if c.isalpha()),
                'numeric': sum(1 for c in all_chars if c.isdigit()),
                'special': sum(1 for c in all_chars if not c.isalnum()),
                'whitespace': sum(1 for c in all_chars if c.isspace())
            },
            'most_common': dict(char_count.most_common(10)),
            'character_classes': {
                'uppercase': sum(1 for c in all_chars if c.isupper()),
                'lowercase': sum(1 for c in all_chars if c.islower()),
                'punctuation': sum(1 for c in all_chars if c in  string.punctuation)
            }
        }