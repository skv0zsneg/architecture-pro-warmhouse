package services

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"smarthome/models"
)

type UpstreamError struct {
	StatusCode int
}

func (e *UpstreamError) Error() string {
	return fmt.Sprintf("devices service returned status %d", e.StatusCode)
}

type DeviceRepository struct {
	baseURL string
	client  *http.Client
}

func NewDeviceRepository(baseURL string) *DeviceRepository {
	return &DeviceRepository{baseURL: baseURL, client: &http.Client{Timeout: 5 * time.Second}}
}

func (r *DeviceRepository) request(ctx context.Context, method, path string, body any, result any) error {
	var payload io.Reader
	if body != nil {
		data, err := json.Marshal(body)
		if err != nil {
			return err
		}
		payload = bytes.NewReader(data)
	}
	req, err := http.NewRequestWithContext(ctx, method, r.baseURL+"/api/v1/devices"+path, payload)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	response, err := r.client.Do(req)
	if err != nil {
		return fmt.Errorf("devices service unavailable: %w", err)
	}
	defer response.Body.Close()
	if response.StatusCode >= 400 {
		return &UpstreamError{StatusCode: response.StatusCode}
	}
	if result != nil {
		return json.NewDecoder(response.Body).Decode(result)
	}
	return nil
}

func (r *DeviceRepository) GetSensors(ctx context.Context) ([]models.Sensor, error) {
	sensors := []models.Sensor{}
	err := r.request(ctx, http.MethodGet, "", nil, &sensors)
	return sensors, err
}

func (r *DeviceRepository) GetSensorByID(ctx context.Context, id int) (models.Sensor, error) {
	var sensor models.Sensor
	err := r.request(ctx, http.MethodGet, fmt.Sprintf("/%d", id), nil, &sensor)
	return sensor, err
}

func (r *DeviceRepository) CreateSensor(ctx context.Context, input models.SensorCreate) (models.Sensor, error) {
	var sensor models.Sensor
	err := r.request(ctx, http.MethodPost, "", input, &sensor)
	return sensor, err
}

func (r *DeviceRepository) UpdateSensor(ctx context.Context, id int, input models.SensorUpdate) (models.Sensor, error) {
	var sensor models.Sensor
	err := r.request(ctx, http.MethodPut, fmt.Sprintf("/%d", id), input, &sensor)
	return sensor, err
}

func (r *DeviceRepository) DeleteSensor(ctx context.Context, id int) error {
	return r.request(ctx, http.MethodDelete, fmt.Sprintf("/%d", id), nil, nil)
}

func (r *DeviceRepository) UpdateSensorValue(ctx context.Context, id int, value float64, status string) error {
	return r.request(ctx, http.MethodPatch, fmt.Sprintf("/%d/value", id), map[string]any{"value": value, "status": status}, nil)
}
