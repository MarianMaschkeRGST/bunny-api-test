# reference
# https://github.com/BunnyWay/bunnystream-api-python

import requests, json, base64

class BunnyCDNStream:

	base_url = "http://video.bunnycdn.com/library/"
	stream_library_id = "359808"
	_api_key = "9cb58b76-8f08-4aac-b4ae8d87074d-7682-4653"
	_headers = {}

	def __init__(self, stream_library_id, api_key):
		self.stream_library_id = stream_library_id
		self._api_key = api_key
		self._headers = {"AccessKey": api_key, "Content-Type": "application/json"}

	def _generate_base_url(self, endpoint):
		return self.base_url + self.stream_library_id + endpoint

	def _check_status_code(self, status):
		"""
			Helper to check response codes.
		"""
		if status == 401:
			raise Exception("Unauthorized; check API key.")
		if status == 404:
			raise Exception("Not found.")

	def get_video(self, video_id):
		"""
			Get specific video information.
		"""
		url = self._generate_base_url("/videos/" + video_id)
		response = requests.get(url, headers=self._headers)
		self._check_status_code(response.status_code)
		try:
			return json.loads(response.text)
		except:
			raise Exception("Failed to retrieve video")

	def list_videos(self, page = 1, per_page = 10, sort_by = "date", search = None, collection_id = None):
		"""
			Lists videos in a library.
		"""
		url = self._generate_base_url("/videos") + "?page=" + str(page) + "&per_page=" + str(per_page) + "&sort_by=" + sort_by
		if search is not None:
			url += "&search=" + search
		if collection_id is not None:
			url += "&collection=" + collection_id
		response = requests.get(url, headers=self._headers)
		self._check_status_code(response.status_code)
		try:
			return json.loads(response.text)
		except:
			raise Exception("Failed to retrieve list of videos")

	def update_video(self, video_id, title = None, collection_id = None):
		"""
			Updates video title or collection.
		"""
		url = self._generate_base_url("/videos/" + video_id)
		payload = {}
		if title is not None:
			payload["title"] = title
		if collection_id is not None:
			payload["collectionId"] = collection_id	 
		response = requests.post(url, data=json.dumps(payload), headers=self._headers)
		self._check_status_code(response.status_code)
		try:
			return json.loads(response.text)
		except:
			raise Exception("Failed to update video")

	def delete_video(self, video_id):
		"""
			Delete video by ID.
		"""
		url = self._generate_base_url("/videos/" + video_id)
		response = requests.delete(url, headers=self._headers)
		self._check_status_code(response.status_code)
		try:
			return json.loads(response.text)
		except:
			raise Exception("Failed to delete video")

	def create_video(self, title, collection_id = None):
		"""
			Create video. (must be done before calling upload_video_with_id())
		"""
		url = self._generate_base_url("/videos")
		payload = {"title": title}
		if collection_id is not None:
			payload["collectionId"] = collection_id
		response = requests.post(url, data=json.dumps(payload), headers=self._headers)
		self._check_status_code(response.status_code)
		try:
			return json.loads(response.text)
		except:
			raise Exception("Failed to create video")

	def upload_video_with_id(self, video_id, path):
		"""
			Uploads video to video_id.
		"""
		url = self._generate_base_url("/videos/" + video_id)
		response = requests.put(url, data=open(path, "rb"), headers=self._headers)
		self._check_status_code(response.status_code)
		try:
			return json.loads(response.text)
		except:
			raise Exception("Failed to upload video")

	def upload_video(self, title, path, collection_id = None):
		"""
			Creates video object and uploads video.
		"""
		resp = self.create_video(title)
		try:
			return self.upload_video_with_id(resp["guid"], path)
		except:
			raise Exception("Failed to upload video")

	def set_video_thumbnail(self, video_id, thumbnail_url):
		"""
			Set video thumbnail from URL.
		"""
		url = self._generate_base_url("/videos/" + video_id + "/thumbnail")
		payload = {"thumbnailUrl": thumbnail_url}
		response = requests.post(url, data=json.dumps(payload), headers=self._headers)
		self._check_status_code(response.status_code)
		try:
			return json.loads(response.text)
		except:
			raise Exception("Failed to set video thumbnail")

	def fetch_video(self, video_id, source, headers = None):
		"""
			Download video from external source; headers = dict{}.
		"""
		url = self._generate_base_url("/videos/" + video_id + "/fetch")
		payload = {"thumbnailUrl": thumbnail_url}
		if headers is not None:
			payload["headers"] = headers
		response = requests.post(url, data=json.dumps(payload), headers=self._headers)
		self._check_status_code(response.status_code)
		try:
			return json.loads(response.text)
		except:
			raise Exception("Failed to fetch video")

	def add_video_captions(self, video_id, language, path, label):
		"""
			Add captions.
		"""
		url = self._generate_base_url("/videos/" + video_id + "/captions/" + language)
		payload = {"captionsFile": base64.b64encode(open(path, "rb").read()).decode("ascii"), "srclang": language, "label": label}
		response = requests.post(url, data=json.dumps(payload), headers=self._headers)
		self._check_status_code(response.status_code)
		try:
			return json.loads(response.text)
		except:
			raise Exception("Failed to add captions")

	def delete_video_captions(self, video_id, language):
		"""
			Delete captions.
		"""
		url = self._generate_base_url("/videos/" + video_id + "/captions/" + language)
		response = requests.delete(url, headers=self._headers)
		self._check_status_code(response.status_code)
		try:
			return json.loads(response.text)
		except:
			raise Exception("Failed to delete captions")