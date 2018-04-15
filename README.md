# PyServer

A simple HTTP web-server in Python3.5+ using asyncio module.

### How to set-up

 - Copy the `server.py` in your main project folder (session.py and logger.py as well if needed)
 - Make a 'static' folder in the main project directory
```
/
server.py
static/
      html/
      css/
      js/
      img/
```

### How to use
- Save all the static files in the 'static' folder
- Import server.py in your web application
- To serve dynamic pages, add routes in your application using `add_route()` function available in server.py

```
Eg:
    def render_form(request, response, id):
        """content may or may not be returned
        """
        return response_content

    server.add_route("GET", "/form/<id>/user", render_form)
```
