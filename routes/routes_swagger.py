from routes import main_blueprint
from .common_imports import *


@main_blueprint.route('/api/openapi.yml', methods=['GET'])
def serve_openapi_yaml():
    """Serve the OpenAPI YAML spec from docs/openapi.yml."""
    try:
        spec_path = os.path.join(current_app.root_path, 'docs', 'openapi.yml')
        if not os.path.exists(spec_path):
            return jsonify({'error': 'OpenAPI spec not found'}), 404
        return current_app.response_class(
            open(spec_path, 'rb').read(),
            mimetype='application/yaml'
        )
    except Exception as e:
        current_app.logger.error(f"Failed to serve openapi.yml: {e}")
        return jsonify({'error': 'Failed to load OpenAPI spec'}), 500


@main_blueprint.route('/api/docs', methods=['GET'])
def swagger_ui():
    """Serve a minimal Swagger UI that points to /api/openapi.yml."""
    # Choose spec URL dynamically: allow override via ?url=, otherwise use absolute URL for current host
    spec_url = request.args.get('url') or url_for('main.serve_openapi_yaml', _external=True)
    html_template = (
        """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
      body { margin: 0; background: #fff; }
      #swagger-ui { max-width: 100%; }
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" crossorigin></script>
    <script>
      window.ui = SwaggerUIBundle({
        url: '__SPEC_URL__',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis],
        layout: 'BaseLayout',
        docExpansion: 'none',
        filter: true,
        defaultModelsExpandDepth: 0,
        defaultModelExpandDepth: 0
      });

      // Enhanced search: extend built-in filter to also match method, path, summary, description, and deeper text
      (function(){
        function normalize(text){ return (text || '').toLowerCase(); }

        function filterOps(query){
          var q = normalize(query || '');
          var root = document.getElementById('swagger-ui');
          if (!root) return;

          var opblocks = root.querySelectorAll('.opblock');
          var tagSections = root.querySelectorAll('.opblock-tag-section');

          // If query is empty, reset any custom filtering and show everything
          if (q.length === 0){
            opblocks.forEach(function(el){ el.style.display = ''; });
            tagSections.forEach(function(section){ section.style.display = ''; });
            return;
          }

          opblocks.forEach(function(el){
            var method = el.querySelector('.opblock-summary-method');
            var path = el.querySelector('.opblock-summary-path');
            var desc = el.querySelector('.opblock-summary-description');
            var tagSection = el.closest('.opblock-tag-section');
            var tagBadge = tagSection ? tagSection.querySelector('.opblock-tag') : null;

            var haystack = [
              method && method.textContent,
              path && path.textContent,
              desc && desc.textContent,
              tagBadge && tagBadge.textContent,
              el.textContent
            ].filter(Boolean).join('\\n');

            var match = normalize(haystack).indexOf(q) !== -1;
            el.style.display = match ? '' : 'none';
          });

          tagSections.forEach(function(section){
            // Do not hide sections if no operations are rendered yet
            var opCount = section.querySelectorAll('.opblock').length;
            if (opCount === 0) return;
            var anyVisible = section.querySelector('.opblock:not([style*="display: none"])');
            section.style.display = anyVisible ? '' : 'none';
          });
        }

        function tryHook(){
          var root = document.getElementById('swagger-ui');
          if (!root) return false;
          var builtin = document.querySelector('.filter .operation-filter-input, input[placeholder*="Filter"]');
          if (!builtin) return false;
          if (builtin.__hooked) return true;
          builtin.__hooked = true;
          var debounceTimeout;
          builtin.addEventListener('input', function(){
            clearTimeout(debounceTimeout);
            var val = builtin.value || '';
            debounceTimeout = setTimeout(function(){ filterOps(val); }, 120);
          });
          filterOps(builtin.value || '');
          return true;
        }

        if (!tryHook()){
          var observerTarget = document.getElementById('swagger-ui');
          if (!observerTarget) return;
          var mo = new MutationObserver(function(){ tryHook(); });
          mo.observe(observerTarget, { childList: true, subtree: true });
        }
      })();
    </script>
  </body>
</html>
        """
    )
    return html_template.replace('__SPEC_URL__', spec_url)


