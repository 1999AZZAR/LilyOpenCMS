import os
import hashlib
import gzip
import mimetypes
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class AssetOptimizer:
    """Asset optimization and management"""
    
    def __init__(self, static_folder: str = "static"):
        self.static_folder = static_folder
        self.compressed_assets = {}
        self.asset_hashes = {}
        self.supported_types = ['css', 'js', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'woff', 'woff2', 'ttf', 'eot']
        self.optimization_ratio = 0.0
        
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get asset optimization statistics"""
        try:
            # Scan static folder for assets
            static_path = Path(self.static_folder)
            if not static_path.exists():
                return self._get_default_stats()
            
            total_files = 0
            compressed_files = 0
            total_size = 0
            compressed_size = 0
            original_files = []
            compressed_files_list = []
            
            # First pass: collect all original files
            for file_path in static_path.rglob('*'):
                if file_path.is_file():
                    file_ext = file_path.suffix.lower().lstrip('.')
                    if file_ext in self.supported_types and not file_path.name.endswith('.gz'):
                        total_files += 1
                        file_size = file_path.stat().st_size
                        total_size += file_size
                        original_files.append(file_path)
                        
                        # Generate hash for versioning
                        self.asset_hashes[str(file_path)] = self._generate_file_hash(file_path)
            
            # Second pass: check for compressed versions
            for original_file in original_files:
                compressed_path = original_file.with_suffix(original_file.suffix + '.gz')
                if compressed_path.exists():
                    compressed_files += 1
                    compressed_size += compressed_path.stat().st_size
                    compressed_files_list.append(compressed_path)
            
            # Calculate optimization ratio based on compressed vs original
            if total_size > 0:
                self.optimization_ratio = compressed_size / total_size if compressed_size > 0 else 0.0
            
            return {
                'compressed_assets_count': compressed_files,
                'total_assets_count': total_files,
                'asset_hashes_count': len(self.asset_hashes),
                'supported_types': self.supported_types,
                'static_folder': self.static_folder,
                'optimization_ratio': self.optimization_ratio,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'compressed_size_mb': round(compressed_size / (1024 * 1024), 2),
                'original_files': [str(f) for f in original_files],
                'compressed_files': [str(f) for f in compressed_files_list]
            }
            
        except Exception as e:
            logger.error(f"Error getting asset stats: {e}")
            return self._get_default_stats()
    
    def _get_default_stats(self) -> Dict[str, Any]:
        """Get default statistics when static folder is not available"""
        return {
            'compressed_assets_count': 0,
            'total_assets_count': 0,
            'asset_hashes_count': 0,
            'supported_types': self.supported_types,
            'static_folder': self.static_folder,
            'optimization_ratio': 0.0,
            'total_size_mb': 0,
            'compressed_size_mb': 0
        }
    
    def _is_compressed(self, file_path: Path) -> bool:
        """Check if file is already compressed"""
        try:
            # Check for gzip compression
            with open(file_path, 'rb') as f:
                magic = f.read(2)
                return magic.startswith(b'\x1f\x8b')
        except:
            return False
    
    def _has_compressed_version(self, file_path: Path) -> bool:
        """Check if a file has a compressed .gz version"""
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        return compressed_path.exists()
    
    def _get_compressed_size(self, file_path: Path) -> int:
        """Get the size of the compressed version of a file"""
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        if compressed_path.exists():
            return compressed_path.stat().st_size
        return 0
    
    def _generate_file_hash(self, file_path: Path) -> str:
        """Generate hash for file versioning"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()[:8]
        except:
            return "00000000"
    
    def compress_assets(self) -> Dict[str, Any]:
        """Compress assets for better performance"""
        try:
            static_path = Path(self.static_folder)
            if not static_path.exists():
                return {'success': False, 'message': 'Static folder not found'}
            
            compressed_count = 0
            total_size_saved = 0
            processed_files = []
            
            # Process CSS files
            for file_path in static_path.rglob('*.css'):
                if not self._is_compressed(file_path):
                    try:
                        # Read original file
                        with open(file_path, 'rb') as f:
                            content = f.read()
                        
                        # Minify CSS (basic minification)
                        minified_content = self._minify_css(content.decode('utf-8'))
                        
                        # Compress content
                        compressed_content = gzip.compress(minified_content.encode('utf-8'), compresslevel=9)
                        
                        # Write compressed file
                        compressed_path = file_path.with_suffix('.css.gz')
                        with open(compressed_path, 'wb') as f:
                            f.write(compressed_content)
                        
                        # Calculate size saved
                        original_size = len(content)
                        compressed_size = len(compressed_content)
                        size_saved = original_size - compressed_size
                        
                        if size_saved > 0:
                            compressed_count += 1
                            total_size_saved += size_saved
                            processed_files.append({
                                'file': str(file_path.name),
                                'original_size': original_size,
                                'compressed_size': compressed_size,
                                'savings_percent': round((size_saved / original_size) * 100, 2)
                            })
                            
                    except Exception as e:
                        logger.error(f"Error compressing {file_path}: {e}")
            
            # Process JS files
            for file_path in static_path.rglob('*.js'):
                if not self._is_compressed(file_path):
                    try:
                        # Read original file
                        with open(file_path, 'rb') as f:
                            content = f.read()
                        
                        # Minify JS (basic minification)
                        minified_content = self._minify_js(content.decode('utf-8'))
                        
                        # Compress content
                        compressed_content = gzip.compress(minified_content.encode('utf-8'), compresslevel=9)
                        
                        # Write compressed file
                        compressed_path = file_path.with_suffix('.js.gz')
                        with open(compressed_path, 'wb') as f:
                            f.write(compressed_content)
                        
                        # Calculate size saved
                        original_size = len(content)
                        compressed_size = len(compressed_content)
                        size_saved = original_size - compressed_size
                        
                        if size_saved > 0:
                            compressed_count += 1
                            total_size_saved += size_saved
                            processed_files.append({
                                'file': str(file_path.name),
                                'original_size': original_size,
                                'compressed_size': compressed_size,
                                'savings_percent': round((size_saved / original_size) * 100, 2)
                            })
                            
                    except Exception as e:
                        logger.error(f"Error compressing {file_path}: {e}")
            
            return {
                'success': True,
                'compressed_count': compressed_count,
                'total_size_saved_mb': round(total_size_saved / (1024 * 1024), 2),
                'message': f'Successfully compressed {compressed_count} files',
                'processed_files': processed_files
            }
            
        except Exception as e:
            logger.error(f"Error in compress_assets: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def _minify_css(self, css_content: str) -> str:
        """Basic CSS minification"""
        # Remove comments
        import re
        css_content = re.sub(r'/\*.*?\*/', '', css_content, flags=re.DOTALL)
        
        # Remove extra whitespace
        css_content = re.sub(r'\s+', ' ', css_content)
        
        # Remove unnecessary semicolons
        css_content = re.sub(r';}', '}', css_content)
        
        # Remove spaces around operators
        css_content = re.sub(r'\s*([{}:;,])\s*', r'\1', css_content)
        
        return css_content.strip()
    
    def _minify_js(self, js_content: str) -> str:
        """Basic JavaScript minification"""
        # Remove single-line comments
        import re
        js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
        
        # Remove multi-line comments
        js_content = re.sub(r'/\*.*?\*/', '', js_content, flags=re.DOTALL)
        
        # Remove extra whitespace
        js_content = re.sub(r'\s+', ' ', js_content)
        
        # Remove unnecessary semicolons
        js_content = re.sub(r';}', '}', js_content)
        
        return js_content.strip()
    
    def clear_asset_cache(self) -> Dict[str, Any]:
        """Clear asset cache and temporary files"""
        try:
            static_path = Path(self.static_folder)
            if not static_path.exists():
                return {'success': False, 'message': 'Static folder not found'}
            
            cleared_count = 0
            
            # Remove compressed files
            for file_path in static_path.rglob('*.gz'):
                try:
                    file_path.unlink()
                    cleared_count += 1
                except Exception as e:
                    logger.error(f"Error removing {file_path}: {e}")
            
            # Clear hash cache
            self.asset_hashes.clear()
            self.compressed_assets.clear()
            
            return {
                'success': True,
                'cleared_count': cleared_count,
                'message': f'Cleared {cleared_count} cached files'
            }
            
        except Exception as e:
            logger.error(f"Error in clear_asset_cache: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def regenerate_hashes(self) -> Dict[str, Any]:
        """Regenerate all asset hashes"""
        try:
            static_path = Path(self.static_folder)
            if not static_path.exists():
                return {'success': False, 'message': 'Static folder not found'}
            
            hash_count = 0
            
            for file_path in static_path.rglob('*'):
                if file_path.is_file():
                    file_ext = file_path.suffix.lower().lstrip('.')
                    if file_ext in self.supported_types:
                        self.asset_hashes[str(file_path)] = self._generate_file_hash(file_path)
                        hash_count += 1
            
            return {
                'success': True,
                'hash_count': hash_count,
                'message': f'Regenerated {hash_count} asset hashes'
            }
            
        except Exception as e:
            logger.error(f"Error in regenerate_hashes: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}

# Global asset optimizer instance
asset_optimizer = None

def get_asset_optimizer():
    """Get the global asset optimizer instance"""
    global asset_optimizer
    if asset_optimizer is None:
        asset_optimizer = AssetOptimizer()
    return asset_optimizer

def get_asset_stats() -> Dict[str, Any]:
    """Get asset optimization statistics for dashboard"""
    try:
        optimizer = get_asset_optimizer()
        stats = optimizer.get_optimization_stats()
        
        # Add additional dashboard-specific stats
        stats.update({
            'asset_hashes_count': len(optimizer.asset_hashes),
            'supported_types': optimizer.supported_types,
            'static_folder': optimizer.static_folder
        })
        
        return stats
    except Exception as e:
        logger.error(f"Error getting asset stats: {e}")
        return {
            'compressed_assets_count': 0,
            'total_assets_count': 0,
            'asset_hashes_count': 0,
            'supported_types': ['css', 'js', 'png', 'jpg', 'jpeg', 'gif', 'svg'],
            'static_folder': 'static',
            'optimization_ratio': 0.0,
            'total_size_mb': 0,
            'compressed_size_mb': 0
        }

def compress_assets_action() -> Dict[str, Any]:
    """Action to compress assets"""
    try:
        optimizer = get_asset_optimizer()
        return optimizer.compress_assets()
    except Exception as e:
        logger.error(f"Error in compress_assets_action: {e}")
        return {'success': False, 'message': f'Error: {str(e)}'}

def clear_asset_cache_action() -> Dict[str, Any]:
    """Action to clear asset cache"""
    try:
        optimizer = get_asset_optimizer()
        return optimizer.clear_asset_cache()
    except Exception as e:
        logger.error(f"Error in clear_asset_cache_action: {e}")
        return {'success': False, 'message': f'Error: {str(e)}'}

def regenerate_hashes_action() -> Dict[str, Any]:
    """Action to regenerate asset hashes"""
    try:
        optimizer = get_asset_optimizer()
        return optimizer.regenerate_hashes()
    except Exception as e:
        logger.error(f"Error in regenerate_hashes_action: {e}")
        return {'success': False, 'message': f'Error: {str(e)}'}