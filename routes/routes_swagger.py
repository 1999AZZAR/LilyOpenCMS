from routes import main_blueprint
from .common_imports import *


@main_blueprint.route('/api/openapi.yml', methods=['GET'])
def serve_openapi_yaml():
    """Serve the OpenAPI YAML spec from docs/openapi.yml."""
    try:
        spec_path = os.path.join(current_app.root_path, 'docs', 'openapi.yml')
        if not os.path.exists(spec_path):
            current_app.logger.error(f"OpenAPI spec file not found at: {spec_path}")
            return jsonify({'error': 'OpenAPI spec not found'}), 404

        # Validate the YAML file before serving
        yaml_error = None
        decode_error = None
        try:
            import yaml
            with open(spec_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            # Additional validation for common issues that cause Swagger UI errors
            if not spec.get('paths'):
                current_app.logger.warning("OpenAPI spec has no paths defined")
            if not spec.get('components', {}).get('schemas'):
                current_app.logger.warning("OpenAPI spec has no schemas defined")

        except ImportError as import_error:
            current_app.logger.error(f"PyYAML not available: {import_error}")
            return jsonify({
                'error': 'YAML processing not available',
                'details': 'PyYAML library is not installed'
            }), 500
        except yaml.YAMLError as yaml_error:
            current_app.logger.error(f"Invalid YAML in OpenAPI spec: {yaml_error}")
        except UnicodeDecodeError as decode_error:
            current_app.logger.error(f"Encoding error in OpenAPI spec: {decode_error}")
        except Exception as validation_error:
            current_app.logger.error(f"Unexpected error during YAML validation: {validation_error}")

        # Return validation errors if any occurred
        if yaml_error:
            return jsonify({
                'error': 'Invalid OpenAPI specification',
                'details': 'The YAML file contains syntax errors',
                'yaml_error': str(yaml_error)
            }), 500
        if decode_error:
            return jsonify({
                'error': 'OpenAPI specification encoding error',
                'details': 'The file cannot be read properly'
            }), 500

        # Serve the file
        return current_app.response_class(
            open(spec_path, 'rb').read(),
            mimetype='application/yaml',
            headers={'Content-Disposition': 'inline; filename="openapi.yml"'}
        )
    except Exception as e:
        current_app.logger.error(f"Failed to serve openapi.yml: {e}", exc_info=True)
        return jsonify({
            'error': 'Failed to load OpenAPI spec',
            'details': str(e)
        }), 500


@main_blueprint.route('/api/openapi.yml/validate', methods=['GET'])
def validate_openapi_spec():
    """Validate the OpenAPI specification and return detailed information."""
    try:
        spec_path = os.path.join(current_app.root_path, 'docs', 'openapi.yml')

        if not os.path.exists(spec_path):
            return jsonify({
                'valid': False,
                'error': 'OpenAPI spec file not found',
                'path': spec_path
            }), 404

        # Import yaml with error handling
        try:
            import yaml
        except ImportError as import_error:
            return jsonify({
                'valid': False,
                'error': 'YAML processing not available',
                'details': 'PyYAML library is not installed',
                'import_error': str(import_error)
            }), 500

        try:
            with open(spec_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)
        except yaml.YAMLError as yaml_error:
            return jsonify({
                'valid': False,
                'error': 'Invalid YAML syntax',
                'details': 'The YAML file contains syntax errors',
                'yaml_error': str(yaml_error)
            }), 500
        except UnicodeDecodeError as decode_error:
            return jsonify({
                'valid': False,
                'error': 'Encoding error',
                'details': 'The file cannot be read properly',
                'decode_error': str(decode_error)
            }), 500

        # Perform comprehensive validation
        validation_result = {
            'valid': True,
            'file_info': {
                'path': spec_path,
                'size': os.path.getsize(spec_path),
                'modified': os.path.getmtime(spec_path)
            },
            'spec_info': {
                'openapi_version': spec.get('openapi'),
                'title': spec.get('info', {}).get('title'),
                'version': spec.get('info', {}).get('version'),
                'description': bool(spec.get('info', {}).get('description')),
                'servers_count': len(spec.get('servers', [])),
                'paths_count': len(spec.get('paths', {})),
                'schemas_count': len(spec.get('components', {}).get('schemas', {})),
                'security_schemes_count': len(spec.get('components', {}).get('securitySchemes', {})),
                'tags_count': len(spec.get('tags', [])),
                'responses_count': len(spec.get('components', {}).get('responses', {}))
            },
            'warnings': [],
            'errors': []
        }

        # Check for common issues
        if not spec.get('paths'):
            validation_result['warnings'].append('No paths defined in the specification')

        if not spec.get('components', {}).get('schemas'):
            validation_result['warnings'].append('No schemas defined in the components section')

        if not spec.get('servers'):
            validation_result['warnings'].append('No server definitions found')

        # Check for potential Swagger UI compatibility issues
        if spec.get('openapi') and spec['openapi'] not in ['3.0.0', '3.0.1', '3.0.2', '3.0.3']:
            validation_result['warnings'].append(f'OpenAPI version {spec["openapi"]} may not be fully supported by Swagger UI')

        return jsonify(validation_result)

    except Exception as e:
        return jsonify({
            'valid': False,
            'error': 'Failed to validate OpenAPI spec',
            'details': str(e)
        }), 500


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
      // Error handler for Swagger UI context issues
      window.addEventListener('error', function(event) {
        if (event.message && event.message.includes("can't access property") &&
            event.message.includes("api") && event.message.includes("C is undefined")) {
          console.warn('Swagger UI context error detected, attempting to fix...');
          event.preventDefault();

          // Show error message to user
          const errorDiv = document.createElement('div');
          errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f44336;
            color: white;
            padding: 15px;
            border-radius: 5px;
            z-index: 9999;
            max-width: 400px;
          `;
          errorDiv.innerHTML = `
            <strong>API Documentation Error</strong><br>
            There was an issue loading the API documentation.
            <br><br>
            <button onclick="location.reload()" style="background: white; color: #f44336; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
              Refresh Page
            </button>
          `;
          document.body.appendChild(errorDiv);

          // Auto-hide after 10 seconds
          setTimeout(() => {
            if (errorDiv.parentNode) {
              errorDiv.parentNode.removeChild(errorDiv);
            }
          }, 10000);
        }
      });

      // Initialize Swagger UI with comprehensive error handling
      try {
        // Check if SwaggerUIBundle is available
        if (typeof SwaggerUIBundle === 'undefined') {
          throw new Error('Swagger UI library not loaded properly');
        }

        window.ui = SwaggerUIBundle({
          url: '__SPEC_URL__',
          dom_id: '#swagger-ui',
          deepLinking: true,
          presets: [SwaggerUIBundle.presets.apis],
          layout: 'BaseLayout',
          docExpansion: 'none',
          filter: true,
          defaultModelsExpandDepth: 0,
          defaultModelExpandDepth: 0,
          // Add timeout and retry options
          requestInterceptor: function(req) {
            // Add timeout to requests
            req.timeout = 10000; // 10 seconds
            return req;
          },
          responseInterceptor: function(res) {
            // Log response for debugging
            if (!res.ok && res.status !== 404) {
              console.warn('Swagger UI received error response:', res.status, res.statusText);
            }
            return res;
          }
        });

        // Test that the UI initialized properly
        setTimeout(() => {
          if (!window.ui || typeof window.ui.getState !== 'function') {
            throw new Error('Swagger UI failed to initialize properly');
          }
        }, 1000);

      } catch (error) {
        console.error('Failed to initialize Swagger UI:', error);

        // Fallback: show comprehensive error message with options
        const container = document.getElementById('swagger-ui');
        if (container) {
          container.innerHTML = `
            <div style="padding: 20px; text-align: center; color: #666; max-width: 600px; margin: 0 auto;">
              <h2 style="color: #f44336;">API Documentation Error</h2>
              <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: left;">
                <strong>Error Details:</strong><br>
                <code style="background: #fff; padding: 10px; display: block; margin: 10px 0; border-radius: 3px;">${error.message}</code>
                <strong>Possible Solutions:</strong>
                <ul style="margin: 10px 0;">
                  <li>• Check browser console for additional errors</li>
                  <li>• Try refreshing the page</li>
                  <li>• Verify the OpenAPI specification is valid</li>
                  <li>• Check if all required dependencies are loaded</li>
                </ul>
              </div>
              <div style="margin: 20px 0;">
                <button onclick="location.reload()" style="background: #007acc; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 0 10px;">
                  🔄 Refresh Page
                </button>
                <button onclick="window.open('/api/openapi.yml/validate', '_blank')" style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 0 10px;">
                  ✅ Validate Spec
                </button>
                <button onclick="window.open('/api/openapi.yml', '_blank')" style="background: #ffc107; color: #000; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 0 10px;">
                  📄 View Raw YAML
                </button>
              </div>
              <p style="font-size: 12px; color: #888; margin-top: 20px;">
                If the problem persists, check the browser console (F12) for more detailed error information.
              </p>
            </div>
          `;
        }
      }

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


