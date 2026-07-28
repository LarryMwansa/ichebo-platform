import os

js_path = 'ichebo-platform/static/js/media_video_upload.js'
template_path = 'ichebo-platform/templates/broadcast/channel_config_form.html'

with open(js_path, 'r') as f:
    js_content = f.read()

with open(template_path, 'r') as f:
    template_content = f.read()

# Replace the script tag and init logic
start_str = '<script src="{% static \'js/media_video_upload.js\' %}?v=2"></script>'
end_str = '</script>'

start_idx = template_content.find(start_str)
end_idx = template_content.find(end_str, start_idx + len(start_str)) + len(end_str)

if start_idx != -1 and end_idx != -1:
    new_script = f"""<script>
// INLINED SCRIPT to avoid ANY caching issues
{js_content}

// Execute immediately since elements are already in the DOM above
LearnVideoUpload.init('-loop');

// Also listen for HTMX load in case the form is injected dynamically later
document.body.addEventListener('htmx:load', function() {{
    LearnVideoUpload.init('-loop');
}});
</script>"""
    
    new_template = template_content[:start_idx] + new_script + template_content[end_idx:]
    with open(template_path, 'w') as f:
        f.write(new_template)
    print("Successfully inlined!")
else:
    print("Could not find script block to replace.")
