package config

import "testing"

func clearMediaEnv(t *testing.T) {
	vars := []string{
		"MEDIA_S3_ENDPOINT", "MEDIA_S3_REGION", "MEDIA_S3_ACCESS_KEY", "MEDIA_S3_SECRET_KEY",
		"MEDIA_UPLOAD_BUCKET", "MEDIA_DELIVERY_BUCKET", "MEDIA_CDN_BASE_URL",
		"MEDIA_DJANGO_WEBHOOK_URL", "MEDIA_DJANGO_API_KEY",
	}
	for _, v := range vars {
		t.Setenv(v, "")
	}
}

func TestValidate_LocalMode_OnlyRequiresWebhookVars(t *testing.T) {
	clearMediaEnv(t)
	t.Setenv("MEDIA_DJANGO_WEBHOOK_URL", "https://app.example.com")
	t.Setenv("MEDIA_DJANGO_API_KEY", "secret")

	cfg := Load()
	if !cfg.LocalMode {
		t.Fatal("expected LocalMode when MEDIA_S3_ENDPOINT is empty")
	}
	if err := cfg.Validate(); err != nil {
		t.Fatalf("expected no error in local mode with webhook vars set, got: %v", err)
	}
}

func TestValidate_MissingWebhookVars_Fails(t *testing.T) {
	clearMediaEnv(t)

	cfg := Load()
	err := cfg.Validate()
	if err == nil {
		t.Fatal("expected error when webhook vars are missing")
	}
}

func TestValidate_S3EndpointSetButOtherS3VarsMissing_Fails(t *testing.T) {
	clearMediaEnv(t)
	t.Setenv("MEDIA_S3_ENDPOINT", "https://s3.example.com")
	t.Setenv("MEDIA_DJANGO_WEBHOOK_URL", "https://app.example.com")
	t.Setenv("MEDIA_DJANGO_API_KEY", "secret")

	cfg := Load()
	if cfg.LocalMode {
		t.Fatal("expected non-local mode when MEDIA_S3_ENDPOINT is set")
	}
	err := cfg.Validate()
	if err == nil {
		t.Fatal("expected error when S3 endpoint is set but other S3 vars are missing")
	}
}

func TestValidate_FullProductionConfig_Passes(t *testing.T) {
	clearMediaEnv(t)
	t.Setenv("MEDIA_S3_ENDPOINT", "https://s3.example.com")
	t.Setenv("MEDIA_S3_REGION", "eu-central")
	t.Setenv("MEDIA_S3_ACCESS_KEY", "key")
	t.Setenv("MEDIA_S3_SECRET_KEY", "secret")
	t.Setenv("MEDIA_UPLOAD_BUCKET", "ics-media-upload")
	t.Setenv("MEDIA_DELIVERY_BUCKET", "ics-media-delivery")
	t.Setenv("MEDIA_CDN_BASE_URL", "https://cdn.example.com")
	t.Setenv("MEDIA_DJANGO_WEBHOOK_URL", "https://app.example.com")
	t.Setenv("MEDIA_DJANGO_API_KEY", "secret")

	cfg := Load()
	if err := cfg.Validate(); err != nil {
		t.Fatalf("expected no error with full production config, got: %v", err)
	}
}
