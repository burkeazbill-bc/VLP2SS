# HTML Formatting Preservation

## Overview

The VLP to ScreenSteps converter now properly handles HTML formatting that is URL-encoded in VLP exports. This ensures that text formatting (bold, italic, code, etc.), special characters, and embedded YouTube videos are correctly preserved during conversion.

## Supported Formatting

The converter automatically detects and converts the following VLP formatting:

| VLP Format | Output Format | Description |
|------------|---------------|-------------|
| `<span class="c5">text</span>` | `<strong>text</strong>` | Bold text |
| `<span class="c3">text</span>` | `<strong>text</strong>` | Bold text (alternate) |
| `<span class="c4">text</span>` | `<em>text</em>` | Italic text |
| `<span class="c6">text</span>` | `<code>text</code>` | Code/monospace text |
| `<span class="c7">text</span>` | `<u>text</u>` | Underlined text |

## Special Characters

Special characters that are double-encoded in VLP exports are properly decoded:

- `&amp;gt;` → `>`
- `&amp;lt;` → `<`
- `&amp;nbsp;` → ` ` (non-breaking space)
- `&amp;amp;` → `&`

## Example

### Before Conversion

VLP XML content:

```xml
&lt;span&gt;Click the '&lt;/span&gt;&lt;span class="c5"&gt;&amp;gt;&lt;/span&gt;&lt;span&gt;' button&lt;/span&gt;
```

### After Conversion

ScreenSteps HTML:

```html
<span>Click the '</span><strong>&gt;</strong><span>' button</span>
```

### Rendered Output

Click the '**>**' button

## Technical Details

### Double HTML Entity Decoding

The converter applies HTML entity decoding twice to handle double-encoded entities that are common in VLP exports.

### VLP CSS Class System

VLP uses numbered CSS classes (c0-c7) for formatting. The converter maps these to semantic HTML tags for better compatibility with ScreenSteps.

## YouTube Video Embeds

The converter automatically detects and converts YouTube video embeds from VLP format to ScreenSteps-compatible iframe embeds.

### VLP Format

```html
<div class="mediatag-thumb youtube-thumb" 
     data-media-id="naK5opxyKWA" 
     data-thumb-url="http://img.youtube.com/vi/naK5opxyKWA/0.jpg">
  ...
</div>
```

### ScreenSteps Format

```html
<div class="html-embed" tabindex="0">
  <div class="fluid-width-video-wrapper" style="padding-top: 56.25%;">
    <iframe src="https://www.youtube.com/embed/naK5opxyKWA" 
            title="YouTube video player" 
            frameborder="0" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
            referrerpolicy="strict-origin-when-cross-origin" 
            allowfullscreen="">
    </iframe>
  </div>
</div>
```

### Features

- Extracts video ID from `data-media-id` attribute
- Falls back to extracting from `data-thumb-url` if needed
- Creates responsive 16:9 aspect ratio container
- Includes all required iframe attributes for modern browsers

## Backward Compatibility

These improvements are fully backward compatible:

- Existing conversion functionality remains unchanged
- Manual, Chapter, and Article creation logic is untouched
- Image embedding and handling is not affected

## Additional Information

For detailed implementation information, see:

- [Python Implementation](../python/vlp_converter.py)
- [Go Implementation](../golang/main.go)
