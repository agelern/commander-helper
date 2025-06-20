import os
import aiohttp
import asyncio
from io import BytesIO
from PIL import Image
from pathlib import Path
import hashlib

class ImageStitcher:
    def __init__(self):
        self.cache_dir = Path(__file__).parent.parent.parent / 'cache' / 'stitched_images'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._session = None

    async def _get_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _download_image(self, url: str) -> Image.Image:
        """Download an image from a URL and return it as a PIL Image."""
        session = await self._get_session()
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Failed to download image: {response.status}")
            data = await response.read()
            return Image.open(BytesIO(data))

    def _get_cache_path(self, urls: list[str]) -> Path:
        """Generate a cache path based on the image URLs."""
        # Create a unique filename based on the URLs
        urls_str = ''.join(urls)
        filename = hashlib.md5(urls_str.encode()).hexdigest()
        # Extension is added when saving
        return self.cache_dir / filename

    async def stitch_partner_images(self, image_urls: list[str]) -> str:
        """
        Stitch two card images side by side and return the cached file path.
        
        Args:
            image_urls: List of URLs for the card images to stitch.
            
        Returns:
            str: Local file path to the stitched image.
        """
        if not image_urls or len(image_urls) != 2:
            raise ValueError("Exactly two image URLs are required")

        cache_path = self._get_cache_path(image_urls).with_suffix('.png')
        
        # Return cached image if it exists
        if cache_path.exists():
            return str(cache_path)

        # Download images
        images = await asyncio.gather(*[self._download_image(url) for url in image_urls])
        
        # Get dimensions
        widths, heights = zip(*(i.size for i in images))
        max_height = max(heights)
        total_width = sum(widths)
        
        # Create output image with transparent background
        stitched = Image.new('RGBA', (total_width, max_height), (0, 0, 0, 0))
        
        # Paste images side-by-side
        x_offset = 0
        for img in images:
            # Convert to RGBA to be safe
            img = img.convert("RGBA")
            # Center vertically if heights differ
            y_offset = (max_height - img.height) // 2
            stitched.paste(img, (x_offset, y_offset))
            x_offset += img.width

        # Save the result as PNG for transparency
        stitched.save(cache_path, 'PNG')
        return str(cache_path)

    async def close(self):
        """Close the aiohttp session."""
        if self._session:
            await self._session.close()
            self._session = None 