import obspython as obs
import urllib.request
import urllib.error

url         = "http://127.0.0.1:5000"
interval    = 1
source_name = ""
stop = 1

# ------------------------------------------------------------

def update_text():
	global url, interval, source_name

	source = obs.obs_get_source_by_name(source_name)
	if source is not None and not stop:
		try:
			settings_source = obs.obs_source_get_settings(source)
			text_source = obs.obs_data_get_string(settings_source, "text")
			if text_source == "00:00:00" or ":" not in text_source:
				text_source = "end_time"
			with urllib.request.urlopen(url + '?source=' + text_source) as response:
				data = response.read()
				text = data.decode('utf-8')

				settings = obs.obs_data_create()
				obs.obs_data_set_string(settings, "text", text)
				obs.obs_source_update(source, settings)
				obs.obs_data_release(settings)

		except urllib.error.URLError as err:
			obs.script_log(obs.LOG_WARNING, "Error opening URL '" + url + "': " + err.reason)
			obs.remove_current_callback()

		obs.obs_source_release(source)

def refresh_pressed(props, prop):
	global stop
	stop = 0
	update_text()

def stop_timer(props, prop):
	global stop
	stop = 1

def reset_timer(props, prop):
	global stop, interval, source_name
	stop = 1

	source = obs.obs_get_source_by_name(source_name)
	if source is not None:
		try:
			settings = obs.obs_data_create()
			obs.obs_data_set_string(settings, "text", "00:00:00")
			obs.obs_source_update(source, settings)
			obs.obs_data_release(settings)

		except error as err:
			obs.script_log(obs.LOG_WARNING, "Error opening URL '" + url + "': " + err.reason)
			obs.remove_current_callback()

		obs.obs_source_release(source)

# ------------------------------------------------------------

def script_description():
	return "Updates a text source to the text retrieved from a URL at every specified interval.\n\nBy Lain"

def script_update(settings):
	global url
	global interval
	global source_name

	source_name = obs.obs_data_get_string(settings, "source")

	obs.timer_remove(update_text)

	if url != "" and source_name != "":
		obs.timer_add(update_text, interval * 1000)

def script_defaults(settings):
	obs.obs_data_set_default_int(settings, "interval", 30)

def script_properties():
	props = obs.obs_properties_create()

	p = obs.obs_properties_add_list(props, "source", "Источник", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
	sources = obs.obs_enum_sources()
	if sources is not None:
		for source in sources:
			source_id = obs.obs_source_get_unversioned_id(source)
			if source_id == "text_gdiplus" or source_id == "text_ft2_source":
				name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(p, name, name)

		obs.source_list_release(sources)

	obs.obs_properties_add_button(props, "button", "Запустить таймер", refresh_pressed)
	obs.obs_properties_add_button(props, "button2", "Остановить таймер", stop_timer)
	obs.obs_properties_add_button(props, "button3", "Обнулить таймер", reset_timer)
	return props
