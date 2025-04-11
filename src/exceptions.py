class APIError(Exception):
  """Raised when there is an issue with an API request."""
  pass

class ConfigurationError(Exception):
  """Raised when there is an issue with the configuration."""
  pass