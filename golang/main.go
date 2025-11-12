package main

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"html"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/fatih/color"
	"github.com/google/uuid"
	"github.com/spf13/cobra"
)

// VLP XML Structures
type Manual struct {
	XMLName             xml.Name     `xml:"Manual"`
	ID                  string       `xml:"id,attr"`
	Name                string       `xml:"name"`
	DefaultLanguageCode string       `xml:"defaultLanguageCode"`
	DataFormat          string       `xml:"dataFormat"`
	ContentNodes        ContentNodes `xml:"contentNodes"`
}

type ContentNodes struct {
	Nodes []ContentNode `xml:"ContentNode"`
}

type ContentNode struct {
	ID            string         `xml:"id,attr"`
	Title         string         `xml:"title"`
	OrderIndex    int            `xml:"orderIndex"`
	Children      *Children      `xml:"children"`
	Localizations *Localizations `xml:"localizations"`
}

type Children struct {
	Nodes []ContentNode `xml:"ContentNode"`
}

type Localizations struct {
	LocaleContent LocaleContent `xml:"LocaleContent"`
}

type LocaleContent struct {
	ID           string  `xml:"id,attr"`
	Title        string  `xml:"title"`
	LanguageCode string  `xml:"languageCode"`
	Content      string  `xml:"content"`
	Images       *Images `xml:"images"`
}

type Images struct {
	Images []Image `xml:"img"`
}

type Image struct {
	Src      string `xml:"src,attr"`
	Filename string `xml:"filename,attr"`
	Width    string `xml:"width,attr"`
	Height   string `xml:"height,attr"`
}

// ScreenSteps JSON Structures
type SSManual struct {
	Manual SSManualData `json:"manual"`
}

type SSManualData struct {
	ID        string      `json:"id"`
	Title     string      `json:"title"`
	Language  string      `json:"language"`
	CreatedAt string      `json:"created_at"`
	UpdatedAt string      `json:"updated_at"`
	Chapters  []SSChapter `json:"chapters"`
}

type SSChapter struct {
	ID          string      `json:"id"`
	Title       string      `json:"title"`
	Order       int         `json:"order"`
	Description string      `json:"description"`
	Articles    []SSArticle `json:"articles"`
}

type SSArticle struct {
	ID       string   `json:"id"`
	Title    string   `json:"title"`
	Position int      `json:"position"`
	VLPOrder int      `json:"vlp_order,omitempty"`
	Steps    []SSStep `json:"steps"`
}

type SSStep struct {
	ID      string  `json:"id"`
	Title   string  `json:"title"`
	Order   int     `json:"order"`
	Content string  `json:"content"`
	Images  []Image `json:"images"`
}

type SSContentBlock struct {
	UUID              string   `json:"uuid"`
	Type              string   `json:"type"`
	Title             string   `json:"title,omitempty"`
	Body              string   `json:"body,omitempty"`
	Depth             int      `json:"depth"`
	SortOrder         int      `json:"sort_order"`
	ContentBlockIDs   []string `json:"content_block_ids,omitempty"`
	AnchorName        string   `json:"anchor_name,omitempty"`
	AutoNumbered      bool     `json:"auto_numbered,omitempty"`
	Foldable          bool     `json:"foldable,omitempty"`
	AssetFileName     string   `json:"asset_file_name,omitempty"`
	ImageAssetID      int      `json:"image_asset_id,omitempty"`
	Width             int      `json:"width,omitempty"`
	Height            int      `json:"height,omitempty"`
	AltTag            string   `json:"alt_tag,omitempty"`
	URL               string   `json:"url,omitempty"`
	Style             string   `json:"style,omitempty"`
	ShowCopyClipboard bool     `json:"show_copy_clipboard,omitempty"`
}

// API Response Structures
type APIManualResponse struct {
	Manual struct {
		ID       int    `json:"id"`
		Title    string `json:"title"`
		Chapters []struct {
			ID       int    `json:"id"`
			Title    string `json:"title"`
			Position int    `json:"position"`
		} `json:"chapters"`
	} `json:"manual"`
}

type APIChapterResponse struct {
	Chapter struct {
		ID       int    `json:"id"`
		Title    string `json:"title"`
		ManualID int    `json:"manual_id"`
	} `json:"chapter"`
}

type APIArticleResponse struct {
	Article struct {
		ID        int    `json:"id"`
		Title     string `json:"title"`
		ChapterID int    `json:"chapter_id"`
	} `json:"article"`
}

type APIImageResponse struct {
	Image struct {
		ID  int    `json:"id"`
		URL string `json:"url"`
	} `json:"image"`
}

type APIErrorResponse struct {
	Error   string `json:"error"`
	RetryIn int    `json:"retry_in"`
}

// Logger with colors
type Logger struct {
	verbose           bool
	logFile           *os.File
	startTime         time.Time
	totalManuals      int
	totalChapters     int
	totalArticles     int
	totalImages       int
	currentManual     int
	currentChapter    int
	currentArticle    int
	processedArticles int
	processedImages   int
}

func NewLogger(verbose bool) (*Logger, error) {
	// Create logs directory
	if err := os.MkdirAll("logs", 0755); err != nil {
		return nil, err
	}

	// Create log file
	timestamp := time.Now().Format("20060102_150405")
	logPath := filepath.Join("logs", fmt.Sprintf("vlp_converter_%s.log", timestamp))
	logFile, err := os.Create(logPath)
	if err != nil {
		return nil, err
	}

	return &Logger{
		verbose:   verbose,
		logFile:   logFile,
		startTime: time.Now(),
	}, nil
}

func (l *Logger) Close() {
	if l.logFile != nil {
		l.logFile.Close()
	}
}

func (l *Logger) Header(message string) {
	header := color.New(color.FgMagenta, color.Bold)
	fmt.Println()
	header.Println(strings.Repeat("=", 70))
	header.Println(center(message, 70))
	header.Println(strings.Repeat("=", 70))
	fmt.Println()
	l.log("HEADER: " + message)
}

func (l *Logger) Success(message string) {
	color.Green("✓ %s", message)
	l.log("SUCCESS: " + message)
}

func (l *Logger) Info(message string) {
	color.Cyan("ℹ %s", message)
	l.log("INFO: " + message)
}

func (l *Logger) Warning(message string) {
	color.Yellow("⚠ %s", message)
	l.log("WARNING: " + message)
}

func (l *Logger) Error(message string) {
	color.Red("✗ %s", message)
	l.log("ERROR: " + message)
}

func (l *Logger) Step(step, total int, message string) {
	color.Blue("[%d/%d] %s", step, total, message)
	l.log(fmt.Sprintf("STEP [%d/%d]: %s", step, total, message))
}

func (l *Logger) Substep(message string) {
	fmt.Printf("  → %s\n", message)
	if l.verbose {
		l.log("SUBSTEP: " + message)
	}
}

func (l *Logger) SetTotals(manuals, chapters, articles, images int) {
	l.totalManuals = manuals
	l.totalChapters = chapters
	l.totalArticles = articles
	l.totalImages = images
}

func (l *Logger) GetProgressString() string {
	manualPct := 0.0
	if l.totalManuals > 0 {
		manualPct = float64(l.currentManual) / float64(l.totalManuals) * 100
	}
	chapterPct := 0.0
	if l.totalChapters > 0 {
		chapterPct = float64(l.currentChapter) / float64(l.totalChapters) * 100
	}
	articlePct := 0.0
	if l.totalArticles > 0 {
		articlePct = float64(l.currentArticle) / float64(l.totalArticles) * 100
	}
	return fmt.Sprintf("[ Manual: %.0f%%, Chapter: %.0f%%, Article: %.0f%% ]", manualPct, chapterPct, articlePct)
}

func (l *Logger) EstimateTimeRemaining() string {
	if l.processedArticles == 0 {
		return "Calculating..."
	}

	// Use weighted formula based on user data
	avgTimePerArticle := 12.5 // seconds
	avgTimePerImage := 2.0    // seconds

	articlesRemaining := l.totalArticles - l.processedArticles
	imagesRemaining := l.totalImages - l.processedImages

	estimatedRemaining := float64(articlesRemaining)*avgTimePerArticle + float64(imagesRemaining)*avgTimePerImage

	minutes := int(estimatedRemaining) / 60
	seconds := int(estimatedRemaining) % 60

	if minutes > 0 {
		return fmt.Sprintf("~%dm %ds", minutes, seconds)
	}
	return fmt.Sprintf("~%ds", seconds)
}

func (l *Logger) Progress(message string) {
	progressStr := l.GetProgressString()
	timeEst := l.EstimateTimeRemaining()
	cyan := color.New(color.FgCyan)
	blue := color.New(color.FgBlue)
	blue.Printf("%s ", progressStr)
	fmt.Printf("%s ", message)
	cyan.Printf("[ETA: %s]\n", timeEst)
	l.log(fmt.Sprintf("%s %s [ETA: %s]", progressStr, message, timeEst))
}

func (l *Logger) log(message string) {
	if l.logFile != nil {
		timestamp := time.Now().Format("2006-01-02 15:04:05")
		l.logFile.WriteString(fmt.Sprintf("%s - %s\n", timestamp, message))
	}
}

// API Client
type APIClient struct {
	account  string
	user     string
	token    string
	baseURL  string
	client   *http.Client
	logger   *Logger
	imageMap map[string]string
}

func NewAPIClient(account, user, token string, logger *Logger) *APIClient {
	return &APIClient{
		account:  account,
		user:     user,
		token:    token,
		baseURL:  fmt.Sprintf("https://%s.screenstepslive.com/api/v2", account),
		client:   &http.Client{Timeout: 60 * time.Second},
		logger:   logger,
		imageMap: make(map[string]string),
	}
}

func (api *APIClient) request(method, endpoint string, body interface{}) (*http.Response, error) {
	url := fmt.Sprintf("%s/%s", api.baseURL, endpoint)

	var reqBody io.Reader
	var jsonData []byte
	if body != nil {
		var err error
		jsonData, err = json.Marshal(body)
		if err != nil {
			return nil, err
		}
		reqBody = bytes.NewBuffer(jsonData)
	}

	// Log request details in verbose mode
	if api.logger.verbose {
		api.logger.Info(strings.Repeat("=", 70))
		api.logger.Info("API REQUEST DETAILS:")
		api.logger.Info(fmt.Sprintf("  Endpoint: %s %s", method, url))
		api.logger.Info(fmt.Sprintf("  Username: %s", api.user))
		if body != nil {
			api.logger.Info(fmt.Sprintf("  JSON Data: %s", string(jsonData)))
		}
		api.logger.Info(strings.Repeat("=", 70))
	}

	for {
		// Recreate request body for retries
		if body != nil {
			reqBody = bytes.NewBuffer(jsonData)
		}

		req, err := http.NewRequest(method, url, reqBody)
		if err != nil {
			return nil, err
		}

		req.SetBasicAuth(api.user, api.token)
		if body != nil {
			req.Header.Set("Content-Type", "application/json")
		}

		resp, err := api.client.Do(req)
		if err != nil {
			api.logger.Error(strings.Repeat("=", 70))
			api.logger.Error("REQUEST ERROR:")
			api.logger.Error(fmt.Sprintf("  Endpoint: %s %s", method, url))
			api.logger.Error(fmt.Sprintf("  Username: %s", api.user))
			if body != nil {
				api.logger.Error(fmt.Sprintf("  Request JSON: %s", string(jsonData)))
			}
			api.logger.Error(fmt.Sprintf("  Error: %v", err))
			api.logger.Error(strings.Repeat("=", 70))
			return nil, err
		}

		// Log response details in verbose mode
		if api.logger.verbose {
			bodyBytes, _ := io.ReadAll(resp.Body)
			resp.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))

			api.logger.Info("API RESPONSE:")
			api.logger.Info(fmt.Sprintf("  Status Code: %d", resp.StatusCode))
			api.logger.Info(fmt.Sprintf("  Body: %s", string(bodyBytes)))
			api.logger.Info(strings.Repeat("=", 70))
		}

		if resp.StatusCode == 200 || resp.StatusCode == 201 {
			// Add 1.25 second delay between successful API calls to avoid rate limiting
			// ScreenSteps rate limit: 8 files per 10 seconds for image uploads
			time.Sleep(1250 * time.Millisecond)
			return resp, nil
		} else if resp.StatusCode == 429 {
			// Rate limit exceeded - check for retry_in value
			var errResp APIErrorResponse
			json.NewDecoder(resp.Body).Decode(&errResp)
			resp.Body.Close()

			retryIn := errResp.RetryIn
			if retryIn == 0 {
				retryIn = 60
			}

			api.logger.Warning(fmt.Sprintf("Rate limit exceeded. Retrying in %d seconds...", retryIn))
			time.Sleep(time.Duration(retryIn) * time.Second)
			// Add additional 1.25 second delay after retry_in
			time.Sleep(1250 * time.Millisecond)
			continue
		} else {
			defer resp.Body.Close()
			bodyBytes, _ := io.ReadAll(resp.Body)

			api.logger.Error(strings.Repeat("=", 70))
			api.logger.Error("API REQUEST FAILED:")
			api.logger.Error(fmt.Sprintf("  Endpoint: %s %s", method, url))
			api.logger.Error(fmt.Sprintf("  Username: %s", api.user))
			api.logger.Error(fmt.Sprintf("  Status Code: %d", resp.StatusCode))
			if body != nil {
				api.logger.Error(fmt.Sprintf("  Request JSON: %s", string(jsonData)))
			}
			api.logger.Error(fmt.Sprintf("  Response: %s", string(bodyBytes)))
			api.logger.Error(strings.Repeat("=", 70))

			return nil, fmt.Errorf("API request failed: %d - %s", resp.StatusCode, string(bodyBytes))
		}
	}
}

func (api *APIClient) CreateManual(siteID, title string, chapters []map[string]interface{}, published bool) (APIManualResponse, error) {
	manualData := map[string]interface{}{
		"title":     title,
		"published": published,
	}

	// Add chapters array if provided
	if len(chapters) > 0 {
		manualData["chapters"] = chapters
	}

	data := map[string]interface{}{
		"manual": manualData,
	}

	resp, err := api.request("POST", fmt.Sprintf("sites/%s/manuals", siteID), data)
	if err != nil {
		return APIManualResponse{}, err
	}
	defer resp.Body.Close()

	var result APIManualResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return APIManualResponse{}, err
	}

	return result, nil
}

func (api *APIClient) CreateChapter(siteID, manualID string, title string, position int) (int, error) {
	data := map[string]interface{}{
		"chapter": map[string]interface{}{
			"position":  position,
			"title":     title,
			"published": true,
			"manual_id": manualID,
		},
	}

	resp, err := api.request("POST", fmt.Sprintf("sites/%s/chapters", siteID), data)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()

	var result APIChapterResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return 0, err
	}

	return result.Chapter.ID, nil
}

func (api *APIClient) CreateArticle(siteID, chapterID string, title string, position int) (int, error) {
	data := map[string]interface{}{
		"article": map[string]interface{}{
			"position":   position,
			"title":      title,
			"published":  true,
			"chapter_id": chapterID,
		},
	}

	resp, err := api.request("POST", fmt.Sprintf("sites/%s/articles", siteID), data)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()

	var result APIArticleResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return 0, err
	}

	return result.Article.ID, nil
}

func (api *APIClient) UploadImage(siteID, articleID string, imagePath string) (map[string]interface{}, error) {
	file, err := os.Open(imagePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add type field (equivalent to curl -F "type=ImageAsset")
	if err := writer.WriteField("type", "ImageAsset"); err != nil {
		return nil, err
	}

	// Add file field (equivalent to curl -F "file=@image.png")
	part, err := writer.CreateFormFile("file", filepath.Base(imagePath))
	if err != nil {
		return nil, err
	}

	if _, err := io.Copy(part, file); err != nil {
		return nil, err
	}
	writer.Close()

	// Use the public Files API endpoint
	url := fmt.Sprintf("%s/sites/%s/files", api.baseURL, siteID)

	// Log request details in verbose mode
	if api.logger.verbose {
		api.logger.Info(strings.Repeat("=", 70))
		api.logger.Info("IMAGE UPLOAD REQUEST:")
		api.logger.Info(fmt.Sprintf("  Endpoint: POST %s", url))
		api.logger.Info(fmt.Sprintf("  Username: %s", api.user))
		api.logger.Info(fmt.Sprintf("  File: %s", filepath.Base(imagePath)))
		api.logger.Info(strings.Repeat("=", 70))
	}

	for {
		// Recreate body for retries
		file.Seek(0, 0)
		body = &bytes.Buffer{}
		writer = multipart.NewWriter(body)

		// Add type field (must be included in every attempt)
		writer.WriteField("type", "ImageAsset")

		// Add file field
		part, _ = writer.CreateFormFile("file", filepath.Base(imagePath))
		io.Copy(part, file)
		writer.Close()

		req, err := http.NewRequest("POST", url, body)
		if err != nil {
			api.logger.Error(strings.Repeat("=", 70))
			api.logger.Error("IMAGE UPLOAD ERROR:")
			api.logger.Error(fmt.Sprintf("  Endpoint: POST %s", url))
			api.logger.Error(fmt.Sprintf("  Username: %s", api.user))
			api.logger.Error(fmt.Sprintf("  File: %s", filepath.Base(imagePath)))
			api.logger.Error(fmt.Sprintf("  Error: %v", err))
			api.logger.Error(strings.Repeat("=", 70))
			return nil, err
		}

		req.SetBasicAuth(api.user, api.token)
		req.Header.Set("Content-Type", writer.FormDataContentType())
		req.Header.Set("Accept", "application/json")

		resp, err := api.client.Do(req)
		if err != nil {
			api.logger.Error(strings.Repeat("=", 70))
			api.logger.Error("IMAGE UPLOAD ERROR:")
			api.logger.Error(fmt.Sprintf("  Endpoint: POST %s", url))
			api.logger.Error(fmt.Sprintf("  Username: %s", api.user))
			api.logger.Error(fmt.Sprintf("  File: %s", filepath.Base(imagePath)))
			api.logger.Error(fmt.Sprintf("  Error: %v", err))
			api.logger.Error(strings.Repeat("=", 70))
			return nil, err
		}

		// Log response in verbose mode
		if api.logger.verbose {
			bodyBytes, _ := io.ReadAll(resp.Body)
			resp.Body = io.NopCloser(bytes.NewBuffer(bodyBytes))

			api.logger.Info("IMAGE UPLOAD RESPONSE:")
			api.logger.Info(fmt.Sprintf("  Status Code: %d", resp.StatusCode))
			api.logger.Info(fmt.Sprintf("  Body: %s", string(bodyBytes)))
			api.logger.Info(strings.Repeat("=", 70))
		}

		if resp.StatusCode == 200 || resp.StatusCode == 201 {
			var result map[string]interface{}
			json.NewDecoder(resp.Body).Decode(&result)
			resp.Body.Close()
			// Add 1.25 second delay between successful API calls to avoid rate limiting
			// ScreenSteps rate limit: 8 files per 10 seconds for image uploads
			time.Sleep(1250 * time.Millisecond)
			return result, nil
		} else if resp.StatusCode == 429 {
			var errResp APIErrorResponse
			json.NewDecoder(resp.Body).Decode(&errResp)
			resp.Body.Close()

			retryIn := errResp.RetryIn
			if retryIn == 0 {
				retryIn = 60
			}

			api.logger.Warning(fmt.Sprintf("Rate limit exceeded. Retrying in %d seconds...", retryIn))
			time.Sleep(time.Duration(retryIn) * time.Second)
			// Add additional 1.25 second delay after retry_in
			time.Sleep(1250 * time.Millisecond)
			continue
		} else {
			defer resp.Body.Close()
			bodyBytes, _ := io.ReadAll(resp.Body)

			api.logger.Error(strings.Repeat("=", 70))
			api.logger.Error("IMAGE UPLOAD FAILED:")
			api.logger.Error(fmt.Sprintf("  Endpoint: POST %s", url))
			api.logger.Error(fmt.Sprintf("  Username: %s", api.user))
			api.logger.Error(fmt.Sprintf("  File: %s", filepath.Base(imagePath)))
			api.logger.Error(fmt.Sprintf("  Status Code: %d", resp.StatusCode))
			api.logger.Error(fmt.Sprintf("  Response: %s", string(bodyBytes)))
			api.logger.Error(strings.Repeat("=", 70))

			return nil, fmt.Errorf("failed to upload image: %d - %s", resp.StatusCode, string(bodyBytes))
		}
	}
}

func (api *APIClient) UpdateArticleContents(siteID, articleID, title string, contentBlocks []map[string]interface{}, publish bool) error {
	data := map[string]interface{}{
		"article": map[string]interface{}{
			"title":          title,
			"content_blocks": contentBlocks,
			"publish":        publish,
		},
	}

	resp, err := api.request("POST", fmt.Sprintf("sites/%s/articles/%s/contents", siteID, articleID), data)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	return nil
}

// HTMLToContentBlocks converts HTML content to ScreenSteps content_blocks format
func HTMLToContentBlocks(htmlContent string) []map[string]interface{} {
	contentBlocks := []map[string]interface{}{}
	sortOrder := 1

	// Simple HTML parsing - split by headers and paragraphs
	// In production, you'd want to use a proper HTML parser
	lines := strings.Split(htmlContent, "\n")
	currentText := ""

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// Check if it's a header
		if strings.HasPrefix(line, "<h") && strings.Contains(line, ">") {
			// Save any accumulated text first
			if currentText != "" {
				contentBlocks = append(contentBlocks, map[string]interface{}{
					"uuid":       fmt.Sprintf("uuid-%d", sortOrder),
					"type":       "TextContent",
					"body":       currentText,
					"depth":      1,
					"sort_order": sortOrder,
				})
				sortOrder++
				currentText = ""
			}

			// Extract header text
			headerText := regexp.MustCompile(`<h[1-6][^>]*>(.*?)</h[1-6]>`).FindStringSubmatch(line)
			if len(headerText) > 1 {
				contentBlocks = append(contentBlocks, map[string]interface{}{
					"uuid":       fmt.Sprintf("uuid-%d", sortOrder),
					"type":       "StepContent",
					"title":      html.UnescapeString(headerText[1]),
					"depth":      0,
					"sort_order": sortOrder,
				})
				sortOrder++
			}
		} else {
			// Accumulate text content
			if currentText != "" {
				currentText += "\n"
			}
			currentText += line
		}
	}

	// Add any remaining text
	if currentText != "" {
		contentBlocks = append(contentBlocks, map[string]interface{}{
			"uuid":       fmt.Sprintf("uuid-%d", sortOrder),
			"type":       "TextContent",
			"body":       currentText,
			"depth":      1,
			"sort_order": sortOrder,
		})
	}

	return contentBlocks
}

// Converter
type Converter struct {
	logger *Logger
}

func NewConverter(logger *Logger) *Converter {
	return &Converter{logger: logger}
}

func (c *Converter) ConvertZip(zipPath, outputDir string, cleanup bool) (string, error) {
	startTime := time.Now()
	c.logger.Header("VLP to ScreenSteps Converter")
	c.logger.Info(fmt.Sprintf("Input: %s", zipPath))
	c.logger.Info(fmt.Sprintf("Output: %s", outputDir))

	// Step 1: Extract ZIP
	c.logger.Step(1, 5, "Extracting VLP ZIP file")
	tempDir, err := c.extractZip(zipPath)
	if err != nil {
		return "", fmt.Errorf("failed to extract ZIP: %w", err)
	}
	if cleanup {
		defer os.RemoveAll(tempDir)
	}

	// Step 2: Parse VLP XML
	c.logger.Step(2, 5, "Parsing VLP content")
	xmlPath := filepath.Join(tempDir, "content.xml")
	manual, err := c.parseXML(xmlPath)
	if err != nil {
		return "", fmt.Errorf("failed to parse XML: %w", err)
	}

	// Step 3: Flatten structure
	c.logger.Step(3, 5, "Flattening content structure")
	chapters := c.flattenStructure(manual)
	c.logger.Substep(fmt.Sprintf("Created %d chapters", len(chapters)))
	totalArticles := 0
	for _, ch := range chapters {
		totalArticles += len(ch.Articles)
	}
	c.logger.Substep(fmt.Sprintf("Created %d articles", totalArticles))

	// Step 4: Convert to ScreenSteps format
	c.logger.Step(4, 5, "Converting to ScreenSteps format")
	ssManual := c.convertToScreenSteps(manual, chapters)

	// Step 5: Write output
	c.logger.Step(5, 5, "Writing output files")
	outputPath := filepath.Join(outputDir, manual.Name)
	articleCount, imageCount, err := c.writeOutput(ssManual, outputPath, tempDir)
	if err != nil {
		return "", fmt.Errorf("failed to write output: %w", err)
	}

	c.logger.Header("Conversion Complete!")
	c.logger.Success(fmt.Sprintf("ScreenSteps content created at: %s", outputPath))
	c.logger.Success(fmt.Sprintf("Converted %d chapters, %d articles, %d images", len(chapters), articleCount, imageCount))

	elapsed := time.Since(startTime)
	c.logger.Info(fmt.Sprintf("Total execution time: %s", elapsed.Round(time.Second)))

	return outputPath, nil
}

func (c *Converter) ConvertDirectory(dirPath, outputDir string) (string, error) {
	startTime := time.Now()
	c.logger.Header("VLP to ScreenSteps Converter")
	c.logger.Info(fmt.Sprintf("Input: %s", dirPath))
	c.logger.Info(fmt.Sprintf("Output: %s", outputDir))

	// Parse VLP XML
	c.logger.Step(1, 4, "Parsing VLP content")
	xmlPath := filepath.Join(dirPath, "content.xml")
	manual, err := c.parseXML(xmlPath)
	if err != nil {
		return "", fmt.Errorf("failed to parse XML: %w", err)
	}

	// Flatten structure
	c.logger.Step(2, 4, "Flattening content structure")
	chapters := c.flattenStructure(manual)
	c.logger.Substep(fmt.Sprintf("Created %d chapters", len(chapters)))

	// Convert to ScreenSteps format
	c.logger.Step(3, 4, "Converting to ScreenSteps format")
	ssManual := c.convertToScreenSteps(manual, chapters)

	// Write output
	c.logger.Step(4, 4, "Writing output files")
	outputPath := filepath.Join(outputDir, manual.Name)
	articleCount, imageCount, err := c.writeOutput(ssManual, outputPath, dirPath)
	if err != nil {
		return "", fmt.Errorf("failed to write output: %w", err)
	}

	c.logger.Header("Conversion Complete!")
	c.logger.Success(fmt.Sprintf("ScreenSteps content created at: %s", outputPath))
	c.logger.Success(fmt.Sprintf("Converted %d chapters, %d articles, %d images", len(chapters), articleCount, imageCount))

	elapsed := time.Since(startTime)
	c.logger.Info(fmt.Sprintf("Total execution time: %s", elapsed.Round(time.Second)))

	return outputPath, nil
}

func (c *Converter) extractZip(zipPath string) (string, error) {
	// Create temp directory
	if err := os.MkdirAll("temp", 0755); err != nil {
		return "", err
	}

	r, err := zip.OpenReader(zipPath)
	if err != nil {
		return "", err
	}
	defer r.Close()

	// Check if all files are in a single root directory
	var rootDir string
	singleRoot := true
	for _, f := range r.File {
		parts := strings.Split(f.Name, string(filepath.Separator))
		if len(parts) > 0 {
			if rootDir == "" {
				rootDir = parts[0]
			} else if parts[0] != rootDir {
				singleRoot = false
				break
			}
		}
	}

	// Determine the target directory
	var tempDir string
	var stripPrefix string

	if singleRoot && rootDir != "" {
		// Extract directly to temp/rootDir, stripping the root folder from ZIP
		tempDir = filepath.Join("temp", rootDir)
		stripPrefix = rootDir + string(filepath.Separator)
	} else {
		// No single root, use ZIP filename as directory
		tempDir = filepath.Join("temp", strings.TrimSuffix(filepath.Base(zipPath), filepath.Ext(zipPath)))
		stripPrefix = ""
	}

	if err := os.MkdirAll(tempDir, 0755); err != nil {
		return "", err
	}

	c.logger.Substep(fmt.Sprintf("Extracting to: %s", tempDir))

	// Extract files
	for _, f := range r.File {
		// Strip the root prefix if needed
		extractPath := f.Name
		if stripPrefix != "" {
			if strings.HasPrefix(f.Name, stripPrefix) {
				extractPath = strings.TrimPrefix(f.Name, stripPrefix)
			} else if f.Name == strings.TrimSuffix(stripPrefix, string(filepath.Separator)) {
				// Skip the root directory itself
				continue
			}
		}

		// Skip if empty path after stripping
		if extractPath == "" {
			continue
		}

		fpath := filepath.Join(tempDir, extractPath)

		if f.FileInfo().IsDir() {
			os.MkdirAll(fpath, os.ModePerm)
			continue
		}

		if err := os.MkdirAll(filepath.Dir(fpath), os.ModePerm); err != nil {
			return "", err
		}

		outFile, err := os.OpenFile(fpath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
		if err != nil {
			return "", err
		}

		rc, err := f.Open()
		if err != nil {
			outFile.Close()
			return "", err
		}

		_, err = io.Copy(outFile, rc)
		outFile.Close()
		rc.Close()

		if err != nil {
			return "", err
		}
	}

	c.logger.Substep(fmt.Sprintf("Extracted %d files", len(r.File)))

	return tempDir, nil
}

func (c *Converter) parseXML(xmlPath string) (*Manual, error) {
	c.logger.Info(fmt.Sprintf("Parsing VLP XML: %s", xmlPath))

	data, err := os.ReadFile(xmlPath)
	if err != nil {
		return nil, err
	}

	var manual Manual
	if err := xml.Unmarshal(data, &manual); err != nil {
		return nil, err
	}

	c.logger.Success(fmt.Sprintf("Parsed manual: %s", manual.Name))
	c.logger.Substep(fmt.Sprintf("Found %d top-level sections", len(manual.ContentNodes.Nodes)))

	return &manual, nil
}

func (c *Converter) flattenStructure(manual *Manual) []SSChapter {
	// First pass: count totals for progress tracking
	totalChapters := 0
	totalArticles := 0
	totalImages := 0

	for idx, chapterNode := range manual.ContentNodes.Nodes {
		// Skip first node if it's just the manual title
		if idx == 0 && (chapterNode.Children == nil || len(chapterNode.Children.Nodes) == 0) {
			continue
		}
		totalChapters++

		if chapterNode.Children != nil {
			totalArticles += len(chapterNode.Children.Nodes)
			for _, articleNode := range chapterNode.Children.Nodes {
				// Count images in article
				totalImages += len(c.getNodeImages(&articleNode))
				// Count images in steps
				if articleNode.Children != nil {
					for _, stepNode := range articleNode.Children.Nodes {
						totalImages += len(c.getNodeImages(&stepNode))
					}
				}
			}
		}
	}

	// Reset and set totals for progress tracking
	c.logger.SetTotals(1, totalChapters, totalArticles, totalImages)
	c.logger.currentManual = 1
	c.logger.currentChapter = 0
	c.logger.currentArticle = 0
	c.logger.processedArticles = 0
	c.logger.processedImages = 0

	var chapters []SSChapter
	chapterIdx := 0

	for idx, chapterNode := range manual.ContentNodes.Nodes {
		// Skip first node if it's just the manual title
		if idx == 0 && (chapterNode.Children == nil || len(chapterNode.Children.Nodes) == 0) {
			continue
		}

		chapterIdx++
		c.logger.currentChapter = chapterIdx

		chapter := SSChapter{
			ID:          chapterNode.ID,
			Title:       chapterNode.Title,
			Order:       chapterNode.OrderIndex,
			Description: c.cleanHTML(c.getNodeContent(&chapterNode)),
			Articles:    []SSArticle{},
		}

		// Process level 2 children as articles
		if chapterNode.Children != nil {
			// Sort articles by VLP order, then assign sequential positions
			articleNodes := chapterNode.Children.Nodes
			position := 1

			for _, articleNode := range articleNodes {
				c.logger.currentArticle++
				c.logger.Progress(fmt.Sprintf("Processing article: %s", articleNode.Title))

				article := SSArticle{
					ID:       articleNode.ID,
					Title:    articleNode.Title,
					VLPOrder: articleNode.OrderIndex,
					Position: position,
					Steps:    []SSStep{},
				}
				position++

				// Process level 3 children as steps
				if articleNode.Children != nil && len(articleNode.Children.Nodes) > 0 {
					for _, stepNode := range articleNode.Children.Nodes {
						step := SSStep{
							ID:      stepNode.ID,
							Title:   stepNode.Title,
							Order:   stepNode.OrderIndex,
							Content: c.cleanHTML(c.getNodeContent(&stepNode)),
							Images:  c.getNodeImages(&stepNode),
						}
						article.Steps = append(article.Steps, step)
						// Count processed images
						c.logger.processedImages += len(c.getNodeImages(&stepNode))
					}
				} else {
					// If no level 3, treat article content as single step
					step := SSStep{
						ID:      articleNode.ID,
						Title:   articleNode.Title,
						Order:   0,
						Content: c.cleanHTML(c.getNodeContent(&articleNode)),
						Images:  c.getNodeImages(&articleNode),
					}
					article.Steps = append(article.Steps, step)
					// Count processed images
					c.logger.processedImages += len(c.getNodeImages(&articleNode))
				}

				chapter.Articles = append(chapter.Articles, article)
				c.logger.processedArticles++
			}
		}

		chapters = append(chapters, chapter)
	}

	return chapters
}

func (c *Converter) getNodeContent(node *ContentNode) string {
	if node.Localizations != nil {
		return node.Localizations.LocaleContent.Content
	}
	return ""
}

func (c *Converter) getNodeImages(node *ContentNode) []Image {
	if node.Localizations != nil && node.Localizations.LocaleContent.Images != nil {
		return node.Localizations.LocaleContent.Images.Images
	}
	return []Image{}
}

func (c *Converter) cleanHTML(htmlContent string) string {
	if htmlContent == "" {
		return ""
	}

	// First unescape HTML entities (may need multiple passes for double-encoding)
	htmlContent = html.UnescapeString(htmlContent)
	// Second pass to handle double-encoded entities like &amp;gt; -> &gt; -> >
	htmlContent = html.UnescapeString(htmlContent)

	// Convert VLP-specific formatting to standard HTML
	htmlContent = c.convertVLPFormatting(htmlContent)

	// Fix image paths
	re := regexp.MustCompile(`src=["']\.\/`)
	htmlContent = re.ReplaceAllString(htmlContent, `src="`)

	return strings.TrimSpace(htmlContent)
}

func (c *Converter) convertVLPFormatting(htmlContent string) string {
	if htmlContent == "" {
		return ""
	}

	// Convert YouTube embeds first (before other transformations)
	htmlContent = c.convertYouTubeEmbeds(htmlContent)

	// Convert VLP paragraph classes to ScreenSteps formatted blocks
	htmlContent = c.convertVLPParagraphStyles(htmlContent)

	// Regex to find all span tags with a class attribute
	spanRegex := regexp.MustCompile(`<span\s+class="([^"]+)"[^>]*>(.*?)</span>`)

	// Map of VLP CSS classes to HTML tags with priority
	classToTagMap := map[string]string{
		"c0": "strong",
		"c3": "strong",
		"c5": "strong",
		"c6": "code",
		"c7": "strong",
	}

	// Replace spans in a single pass to handle priorities correctly
	htmlContent = spanRegex.ReplaceAllStringFunc(htmlContent, func(match string) string {
		submatches := spanRegex.FindStringSubmatch(match)
		if len(submatches) < 3 {
			return match // Should not happen with a valid match
		}
		classes := strings.Fields(submatches[1])
		content := submatches[2]

		var replacementTag string

		// Prioritize 'c5' (strong) over other classes
		for _, class := range classes {
			if class == "c5" {
				replacementTag = "strong"
				break
			}
		}

		// If c5 is not found, use the first match from the map
		if replacementTag == "" {
			for _, class := range classes {
				if tag, ok := classToTagMap[class]; ok {
					replacementTag = tag
					break
				}
			}
		}

		if replacementTag != "" {
			return fmt.Sprintf("<%s>%s</%s>", replacementTag, content, replacementTag)
		}

		// If no mapping is found (e.g., class="c0"), unwrap the span
		return content
	})

	// Clean up any remaining empty spans
	emptySpanPattern := regexp.MustCompile(`<span[^>]*>\s*</span>`)
	htmlContent = emptySpanPattern.ReplaceAllString(htmlContent, "")

	// Normalize <ol> start attributes by removing them
	olStartPattern := regexp.MustCompile(`(<ol[^>]*) start="[^"]*"`)
	htmlContent = olStartPattern.ReplaceAllString(htmlContent, "$1")

	return htmlContent
}

func (c *Converter) convertVLPParagraphStyles(htmlContent string) string {
	// Map of VLP paragraph classes to ScreenSteps styles
	pClassToStyleMap := map[string]string{
		"c10": "introduction",
		"c44": "introduction",
		"c48": "info",
		// Add other mappings here as they are identified
	}

	for pClass, style := range pClassToStyleMap {
		// Regex to find one or more consecutive <p> tags with the specific class,
		// allowing for other classes to be present.
		// It also handles optional whitespace between the p tags.
		groupPattern := fmt.Sprintf(`(?s)((?:<p\s+class="[^"]*\b%s\b[^"]*".*?</p>\s*)+)`, pClass)
		groupRegex := regexp.MustCompile(groupPattern)

		htmlContent = groupRegex.ReplaceAllStringFunc(htmlContent, func(match string) string {
			// Extract individual p tags from the matched group
			pTagPattern := fmt.Sprintf(`(?s)<p\s+class="[^"]*\b%s\b[^"]*".*?</p>`, pClass)
			pTagExtractor := regexp.MustCompile(pTagPattern)
			pTags := pTagExtractor.FindAllString(match, -1)

			var contentBuilder strings.Builder
			var imageOnlyBuilder strings.Builder
			hasContent := false

			// Concatenate non-empty paragraphs
			// Styled blocks should only contain text content, not standalone images
			for _, pTag := range pTags {
				// Check if the paragraph has meaningful text content
				tagContentRegex := regexp.MustCompile(`(?s)<p[^>]*>(.*)</p>`)
				submatches := tagContentRegex.FindStringSubmatch(pTag)
				if len(submatches) > 1 {
					// Strip tags to check for text content
					content := regexp.MustCompile(`<[^>]+>`).ReplaceAllString(submatches[1], "")
					content = strings.TrimSpace(content)

					// Only include paragraphs with actual text content in styled block
					if content != "" {
						contentBuilder.WriteString(pTag)
						hasContent = true
					} else if strings.Contains(pTag, "<img") {
						// Preserve image-only paragraphs outside the styled block
						imageOnlyBuilder.WriteString(pTag)
					}
					// Empty paragraphs with no text and no images are discarded
				}
			}

			// Build the result
			var result strings.Builder

			// If we have text content, wrap it in a styled div
			if hasContent {
				result.WriteString(fmt.Sprintf(
					`<div class="screensteps-styled-block" data-style="%s">%s</div>`,
					style,
					contentBuilder.String(),
				))
			}

			// Append any image-only paragraphs after the styled block
			if imageOnlyBuilder.Len() > 0 {
				result.WriteString(imageOnlyBuilder.String())
			}

			// If we have neither text content nor images, return empty string to remove the block
			if !hasContent && imageOnlyBuilder.Len() == 0 {
				return ""
			}

			return result.String()
		})
	}
	return htmlContent
}

func (c *Converter) convertYouTubeEmbeds(htmlContent string) string {
	// Pattern to match VLP YouTube embed divs
	// Example: <div class="mediatag-thumb youtube-thumb" ... data-media-id="naK5opxyKWA" ...>
	youtubePattern := regexp.MustCompile(`<div[^>]*class="[^"]*mediatag-thumb youtube-thumb[^"]*"[^>]*data-media-id="([^"]+)"[^>]*>.*?</div>`)

	// Find all matches
	matches := youtubePattern.FindAllStringSubmatch(htmlContent, -1)

	for _, match := range matches {
		if len(match) >= 2 {
			fullMatch := match[0]
			videoID := match[1]

			// Create ScreenSteps-compatible HTML embed structure
			// Format: <div class="html-embed"><iframe width="560" height="315" ...></iframe></div>
			screenStepsEmbed := fmt.Sprintf(
				`<div class="html-embed">`+
					`<iframe width="560" height="315" src="https://www.youtube.com/embed/%s" title="YouTube video player" frameborder="0" `+
					`allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" `+
					`referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>`,
				videoID,
			)

			// Replace the VLP YouTube div with ScreenSteps format
			htmlContent = strings.Replace(htmlContent, fullMatch, screenStepsEmbed, 1)

			c.logger.Substep(fmt.Sprintf("Converted YouTube embed: %s", videoID))
		}
	}

	// Fallback: Try to extract video ID from data-thumb-url if data-media-id is not found
	thumbUrlPattern := regexp.MustCompile(`<div[^>]*class="[^"]*mediatag-thumb youtube-thumb[^"]*"[^>]*data-thumb-url="[^"]*youtube\.com/vi/([^/]+)/[^"]*"[^>]*>.*?</div>`)
	thumbMatches := thumbUrlPattern.FindAllStringSubmatch(htmlContent, -1)

	for _, match := range thumbMatches {
		if len(match) >= 2 {
			fullMatch := match[0]
			videoID := match[1]

			// Only process if not already converted
			if strings.Contains(fullMatch, "mediatag-thumb") {
				// Create ScreenSteps-compatible HTML embed structure
				// Format: <div class="html-embed"><iframe width="560" height="315" ...></iframe></div>
				screenStepsEmbed := fmt.Sprintf(
					`<div class="html-embed">`+
						`<iframe width="560" height="315" src="https://www.youtube.com/embed/%s" title="YouTube video player" frameborder="0" `+
						`allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" `+
						`referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>`,
					videoID,
				)

				htmlContent = strings.Replace(htmlContent, fullMatch, screenStepsEmbed, 1)

				c.logger.Substep(fmt.Sprintf("Converted YouTube embed (from thumb URL): %s", videoID))
			}
		}
	}

	return htmlContent
}

func (c *Converter) extractDescription(htmlContent string, maxLength int) string {
	if htmlContent == "" {
		return ""
	}

	// Remove HTML tags
	re := regexp.MustCompile(`<[^>]+>`)
	text := re.ReplaceAllString(htmlContent, "")

	// Remove extra whitespace
	re = regexp.MustCompile(`\s+`)
	text = re.ReplaceAllString(text, " ")
	text = strings.TrimSpace(text)

	if len(text) > maxLength {
		text = text[:maxLength] + "..."
	}

	return text
}

func (c *Converter) convertToScreenSteps(manual *Manual, chapters []SSChapter) SSManual {
	return SSManual{
		Manual: SSManualData{
			ID:        manual.ID,
			Title:     manual.Name,
			Language:  manual.DefaultLanguageCode,
			CreatedAt: time.Now().Format(time.RFC3339),
			UpdatedAt: time.Now().Format(time.RFC3339),
			Chapters:  chapters,
		},
	}
}

func (c *Converter) writeOutput(manual SSManual, outputPath, sourceDir string) (int, int, error) {
	c.logger.Info("Writing ScreenSteps output files...")

	// Create directory structure
	articlesDir := filepath.Join(outputPath, "articles")
	imagesDir := filepath.Join(outputPath, "images")

	if err := os.MkdirAll(articlesDir, 0755); err != nil {
		return 0, 0, err
	}
	if err := os.MkdirAll(imagesDir, 0755); err != nil {
		return 0, 0, err
	}

	// Write TOC
	tocFile := filepath.Join(outputPath, manual.Manual.ID+".json")
	if err := c.writeJSON(tocFile, manual); err != nil {
		return 0, 0, err
	}
	c.logger.Substep(fmt.Sprintf("Created TOC: %s", filepath.Base(tocFile)))

	// Write articles and count images
	articleCount := 0
	imageCount := 0
	for _, chapter := range manual.Manual.Chapters {
		for _, article := range chapter.Articles {
			// Write article JSON (with steps)
			articleFile := filepath.Join(articlesDir, article.ID+".json")
			if err := c.writeJSON(articleFile, article); err != nil {
				return 0, 0, err
			}

			// Copy images from steps
			articleImagesDir := filepath.Join(imagesDir, article.ID)
			if err := os.MkdirAll(articleImagesDir, 0755); err != nil {
				return 0, 0, err
			}

			for _, step := range article.Steps {
				for _, img := range step.Images {
					// Extract just the base filename (remove any directory prefix like "images/")
					baseFilename := filepath.Base(img.Filename)

					// Find the image recursively within the images directory
					srcImage := findImageRecursive(filepath.Join(sourceDir, "images"), baseFilename)
					dstImage := filepath.Join(articleImagesDir, baseFilename)

					c.logger.Substep(fmt.Sprintf("  Attempting to copy image: %s", img.Filename))
					c.logger.Substep(fmt.Sprintf("    Base filename: %s", baseFilename))
					c.logger.Substep(fmt.Sprintf("    Source: %s", srcImage))
					c.logger.Substep(fmt.Sprintf("    Destination: %s", dstImage))

					if srcImage == "" {
						c.logger.Warning(fmt.Sprintf("Source image not found for copy: %s (referenced in chapter: %s, article: %s, step: %s)",
							img.Filename, chapter.Title, article.Title, step.Title))
						continue
					}

					if err := copyFile(srcImage, dstImage); err != nil {
						c.logger.Warning(fmt.Sprintf("Failed to copy image %s to %s: %v", srcImage, dstImage, err))
					} else {
						c.logger.Substep(fmt.Sprintf("    Copied: %s", baseFilename))
						imageCount++
					}
				}
			}

			articleCount++
		}
	}

	c.logger.Substep(fmt.Sprintf("Created %d article files with %d images", articleCount, imageCount))
	c.logger.Success(fmt.Sprintf("Output written to: %s", outputPath))

	return articleCount, imageCount, nil
}

func (c *Converter) writeJSON(filename string, data interface{}) error {
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	encoder.SetEscapeHTML(false)

	return encoder.Encode(data)
}

// SkippedImage tracks images that were not found during upload
type SkippedImage struct {
	ImagePath    string
	ChapterTitle string
	ArticleTitle string
	StepTitle    string
}

// Uploader
func UploadToScreenSteps(contentDir, account, user, token, siteID string, logger *Logger, suffix bool) error {
	startTime := time.Now()
	logger.Header("ScreenSteps Content Uploader")
	logger.Info(fmt.Sprintf("Content directory: %s", contentDir))
	logger.Info(fmt.Sprintf("Target site ID: %s", siteID))

	// Track skipped images
	var skippedImages []SkippedImage

	// Track uploaded images
	uploadedImagesCount := 0

	// Create API client
	api := NewAPIClient(account, user, token, logger)

	// Step 1: Load content
	logger.Step(1, 5, "Loading converted content")
	tocFile, err := findTOCFile(contentDir)
	if err != nil {
		return err
	}

	data, err := os.ReadFile(tocFile)
	if err != nil {
		return err
	}

	var manual SSManual
	if err := json.Unmarshal(data, &manual); err != nil {
		return err
	}

	logger.Substep(fmt.Sprintf("Manual: %s", manual.Manual.Title))
	logger.Substep(fmt.Sprintf("Chapters: %d", len(manual.Manual.Chapters)))

	// Count totals for progress tracking
	totalChapters := len(manual.Manual.Chapters)
	totalArticles := 0
	totalImages := 0
	for _, chapter := range manual.Manual.Chapters {
		totalArticles += len(chapter.Articles)
		for _, article := range chapter.Articles {
			for _, step := range article.Steps {
				totalImages += len(step.Images)
			}
		}
	}

	// Reset and set totals for progress tracking (fresh start for upload phase)
	logger.SetTotals(1, totalChapters, totalArticles, totalImages)
	logger.currentManual = 1
	logger.currentChapter = 0
	logger.currentArticle = 0
	logger.processedArticles = 0
	logger.processedImages = 0
	logger.startTime = time.Now() // Reset start time for upload phase

	// Step 2: Create manual with chapters
	logger.Step(2, 4, "Creating manual with chapters in ScreenSteps")

	// Prepare chapters array for manual creation
	chaptersArray := []map[string]interface{}{}
	for _, chapter := range manual.Manual.Chapters {
		chaptersArray = append(chaptersArray, map[string]interface{}{
			"position":  chapter.Order,
			"title":     chapter.Title,
			"published": true,
		})
	}

	manualTitle := manual.Manual.Title
	if suffix {
		manualTitle += "-go"
	}
	// Create manual with all chapters in one call
	manualResp, err := api.CreateManual(siteID, manualTitle, chaptersArray, false)
	if err != nil {
		return fmt.Errorf("failed to create manual: %w", err)
	}
	manualID := manualResp.Manual.ID
	logger.Success(fmt.Sprintf("Created manual: %s (ID: %d)", manual.Manual.Title, manualID))

	// Map old chapter IDs to new chapter IDs from response
	chapterMap := make(map[string]int)
	if len(manualResp.Manual.Chapters) > 0 {
		for i, chapter := range manual.Manual.Chapters {
			if i < len(manualResp.Manual.Chapters) {
				chapterMap[chapter.ID] = manualResp.Manual.Chapters[i].ID
				logger.Substep(fmt.Sprintf("Created chapter: %s", manualResp.Manual.Chapters[i].Title))
			}
		}
	}

	// Step 3: Create articles, upload images, and add content
	logger.Step(3, 4, "Creating articles and adding content")

	for chapterIdx, chapter := range manual.Manual.Chapters {
		logger.currentChapter = chapterIdx + 1
		chapterID := chapterMap[chapter.ID]

		for _, article := range chapter.Articles {
			logger.currentArticle++
			logger.Progress(fmt.Sprintf("Creating article: %s", article.Title))

			// Create article placeholder
			articleID, err := api.CreateArticle(
				siteID,
				fmt.Sprintf("%d", chapterID),
				article.Title,
				article.Position,
			)
			if err != nil {
				logger.Warning(fmt.Sprintf("Failed to create article %s: %v", article.Title, err))
				continue
			}

			// Generate content blocks from steps
			contentBlocks := []map[string]interface{}{}
			sortOrder := 1

			// Images directory for this article
			imagesDir := filepath.Join(contentDir, "images", article.ID)

			for _, step := range article.Steps {
				// Create StepContent block
				stepUUID := generateUUID()
				stepBlock := map[string]interface{}{
					"uuid":              stepUUID,
					"type":              "StepContent",
					"title":             step.Title,
					"depth":             0,
					"sort_order":        sortOrder,
					"content_block_ids": []string{},
					"anchor_name":       slugify(step.Title),
					"auto_numbered":     false,
					"foldable":          false,
				}
				contentBlocks = append(contentBlocks, stepBlock)
				sortOrder++

				// New sequential parsing logic to preserve content order
				blockRegex := regexp.MustCompile(`(?s)(<div class="html-embed">.*?</div>|<div class="screensteps-styled-block"[^>]*>.*?</div>|<img[^>]+src="[^"]+"[^>]*>)`)
				indexes := blockRegex.FindAllStringSubmatchIndex(step.Content, -1)
				lastIndex := 0

				imgTagRegex := regexp.MustCompile(`<img[^>]+src="([^"]+)"[^>]*>`)
				styledBlockRegex := regexp.MustCompile(`<div class="screensteps-styled-block"[^>]*data-style="([^"]+)"[^>]*>(.*?)</div>`)

				for _, matchIndexes := range indexes {
					start, end := matchIndexes[0], matchIndexes[1]

					// 1. Process text before the special block
					textBefore := step.Content[lastIndex:start]
					plainTextBefore := regexp.MustCompile(`<[^>]+>`).ReplaceAllString(textBefore, "")
					if strings.TrimSpace(plainTextBefore) != "" {
						textUUID := generateUUID()
						textBlock := map[string]interface{}{
							"uuid":                textUUID,
							"type":                "TextContent",
							"body":                textBefore,
							"depth":               1,
							"sort_order":          sortOrder,
							"style":               nil,
							"show_copy_clipboard": false,
						}
						contentBlocks = append(contentBlocks, textBlock)
						stepBlock["content_block_ids"] = append(stepBlock["content_block_ids"].([]string), textUUID)
						sortOrder++
					}

					// 2. Process the special block itself
					blockHTML := step.Content[start:end]

					if strings.HasPrefix(blockHTML, "<img") {
						// Image Block
						imgMatches := imgTagRegex.FindStringSubmatch(blockHTML)
						if len(imgMatches) > 1 {
							src := html.UnescapeString(imgMatches[1])
							srcPath := src
							if idx := strings.Index(src, "?"); idx != -1 {
								srcPath = src[:idx]
							}
							filename := filepath.Base(srcPath)

							imagePath := filepath.Join(imagesDir, filename)
							if _, err := os.Stat(imagePath); err == nil {
								imageResponse, err := api.UploadImage(siteID, fmt.Sprintf("%d", articleID), imagePath)
								if err != nil {
									logger.Warning(fmt.Sprintf("Failed to upload image %s: %v", filename, err))
									skippedImages = append(skippedImages, SkippedImage{
										ImagePath: imagePath, ChapterTitle: chapter.Title, ArticleTitle: article.Title, StepTitle: step.Title,
									})
								} else if fileData, ok := imageResponse["file"].(map[string]interface{}); ok {
									if imageAssetID, ok := fileData["id"].(float64); ok {
										// Create ImageContentBlock
										imageUUID := generateUUID()
										imageBlock := map[string]interface{}{
											"uuid": imageUUID, "type": "ImageContentBlock", "asset_file_name": filename, "image_asset_id": int(imageAssetID),
											"width": int(fileData["width"].(float64)), "height": int(fileData["height"].(float64)), "depth": 1, "sort_order": sortOrder,
											"alt_tag": "", "url": fileData["url"].(string),
										}
										contentBlocks = append(contentBlocks, imageBlock)
										stepBlock["content_block_ids"] = append(stepBlock["content_block_ids"].([]string), imageUUID)
										sortOrder++
										uploadedImagesCount++
									}
								}
							} else {
								logger.Warning(fmt.Sprintf("Image not found, skipping: %s", imagePath))
								skippedImages = append(skippedImages, SkippedImage{
									ImagePath: imagePath, ChapterTitle: chapter.Title, ArticleTitle: article.Title, StepTitle: step.Title,
								})
							}
						}
					} else if strings.HasPrefix(blockHTML, `<div class="html-embed"`) {
						// YouTube Embed Block
						embedUUID := generateUUID()
						embedBlock := map[string]interface{}{
							"uuid": embedUUID, "type": "TextContent", "body": blockHTML, "depth": 1, "sort_order": sortOrder,
							"style": "html-embed", "show_copy_clipboard": false,
						}
						contentBlocks = append(contentBlocks, embedBlock)
						stepBlock["content_block_ids"] = append(stepBlock["content_block_ids"].([]string), embedUUID)
						sortOrder++
					} else if strings.HasPrefix(blockHTML, `<div class="screensteps-styled-block"`) {
						// Styled Block
						styleMatches := styledBlockRegex.FindStringSubmatch(blockHTML)
						if len(styleMatches) > 2 {
							style := styleMatches[1]
							innerBody := styleMatches[2]
							blockUUID := generateUUID()
							block := map[string]interface{}{
								"uuid": blockUUID, "type": "TextContent", "body": innerBody, "depth": 1, "sort_order": sortOrder,
								"style": style, "show_copy_clipboard": false,
							}
							contentBlocks = append(contentBlocks, block)
							stepBlock["content_block_ids"] = append(stepBlock["content_block_ids"].([]string), blockUUID)
							sortOrder++
						}
					}
					lastIndex = end
				}

				// 3. Process any remaining text after the last special block
				remainingText := step.Content[lastIndex:]
				plainRemainingText := regexp.MustCompile(`<[^>]+>`).ReplaceAllString(remainingText, "")
				if strings.TrimSpace(plainRemainingText) != "" {
					textUUID := generateUUID()
					textBlock := map[string]interface{}{
						"uuid": textUUID, "type": "TextContent", "body": remainingText, "depth": 1, "sort_order": sortOrder,
						"style": nil, "show_copy_clipboard": false,
					}
					contentBlocks = append(contentBlocks, textBlock)
					stepBlock["content_block_ids"] = append(stepBlock["content_block_ids"].([]string), textUUID)
					sortOrder++
				}
			}

			// Update article contents
			err = api.UpdateArticleContents(siteID, fmt.Sprintf("%d", articleID), article.Title, contentBlocks, true)
			if err != nil {
				logger.Warning(fmt.Sprintf("Failed to update article contents %s: %v", article.Title, err))
			}

			// Track processed articles and images
			logger.processedArticles++
			for _, step := range article.Steps {
				logger.processedImages += len(step.Images)
			}
		}
	}

	// Final progress update
	logger.Progress("Upload complete!")

	logger.Step(4, 4, "Upload complete")
	logger.Success(fmt.Sprintf("Created %d articles", logger.processedArticles))

	logger.Header("Upload Complete!")
	logger.Success(fmt.Sprintf("Manual: %s", manual.Manual.Title))
	logger.Success(fmt.Sprintf("Manual ID: %d", manualID))
	logger.Success(fmt.Sprintf("Articles uploaded: %d", logger.processedArticles))
	logger.Success(fmt.Sprintf("Images uploaded: %d", uploadedImagesCount))
	if len(skippedImages) > 0 {
		logger.Warning(fmt.Sprintf("Images skipped: %d", len(skippedImages)))
	} else {
		logger.Success("Images skipped: 0")
	}

	// Display skipped images summary
	if len(skippedImages) > 0 {
		logger.Header("Skipped Images Summary")
		logger.Warning(fmt.Sprintf("Total images skipped: %d", len(skippedImages)))
		logger.Info("Images were replaced with alert: ERROR IMPORTING IMAGE - PLEASE RE-CREATE SCREENSHOT")
		fmt.Println()

		// Group by chapter
		chapterMap := make(map[string][]SkippedImage)
		for _, img := range skippedImages {
			chapterMap[img.ChapterTitle] = append(chapterMap[img.ChapterTitle], img)
		}

		// Display grouped by chapter and article
		for chapterTitle, images := range chapterMap {
			logger.Info(fmt.Sprintf("Chapter: %s", chapterTitle))

			// Group by article within chapter
			articleMap := make(map[string][]SkippedImage)
			for _, img := range images {
				articleMap[img.ArticleTitle] = append(articleMap[img.ArticleTitle], img)
			}

			for articleTitle, articleImages := range articleMap {
				logger.Substep(fmt.Sprintf("  Article: %s", articleTitle))
				for _, img := range articleImages {
					logger.Substep(fmt.Sprintf("    Step: %s", img.StepTitle))
					logger.Substep(fmt.Sprintf("      Image: %s", filepath.Base(img.ImagePath)))
				}
			}
			fmt.Println()
		}
	}

	elapsed := time.Since(startTime)
	logger.Info(fmt.Sprintf("Total execution time: %s", elapsed.Round(time.Second)))

	return nil
}

// Utility functions
func center(s string, width int) string {
	if len(s) >= width {
		return s
	}
	padding := (width - len(s)) / 2
	return strings.Repeat(" ", padding) + s
}

func copyFile(src, dst string) error {
	sourceFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer sourceFile.Close()

	destFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer destFile.Close()

	_, err = io.Copy(destFile, sourceFile)
	return err
}

// findImageRecursive searches for a file with the given filename within a root directory and its subdirectories.
func findImageRecursive(rootDir, filename string) string {
	var foundPath string
	filepath.Walk(rootDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() && info.Name() == filename {
			foundPath = path
			return filepath.SkipDir // Found the file, stop walking
		}
		return nil
	})
	return foundPath
}

func findTOCFile(contentDir string) (string, error) {
	files, err := os.ReadDir(contentDir)
	if err != nil {
		return "", err
	}

	for _, file := range files {
		if !file.IsDir() && strings.HasSuffix(file.Name(), ".json") && file.Name() != "manifest.json" {
			return filepath.Join(contentDir, file.Name()), nil
		}
	}

	return "", fmt.Errorf("no TOC file found in %s", contentDir)
}

func printExamples() {
	examples := `
╔══════════════════════════════════════════════════════════════════════════╗
║                         USAGE EXAMPLES                                   ║
╚══════════════════════════════════════════════════════════════════════════╝

1. Convert a VLP ZIP file:
   ./vlp2ss -i HOL-2601-03-VCF-L_en.zip -o output/

2. Convert an extracted VLP directory:
   ./vlp2ss -i VLP-Export-Samples/HOL-2601-03-VCF-L-en/ -o output/

3. Convert with verbose logging:
   ./vlp2ss -i input.zip -o output/ -v

4. Convert and upload to ScreenSteps:
   ./vlp2ss -i input.zip -o output/ \
       --upload \
       --account myaccount \
       --user admin \
       --token YOUR_API_TOKEN \
       --site 12345

5. Keep temporary files for debugging:
   ./vlp2ss -i input.zip -o output/ --no-cleanup

6. Batch convert multiple files:
   for file in *.zip; do
       ./vlp2ss -i "$file" -o output/
   done

╔══════════════════════════════════════════════════════════════════════════╗
║                         BUILDING FROM SOURCE                             ║
╚══════════════════════════════════════════════════════════════════════════╝

# Download dependencies
go mod tidy

# Build the binary
go build -o vlp2ss main.go

# Or use Makefile
make build

# Run the converter
./vlp2ss -i input.zip -o output/

╔══════════════════════════════════════════════════════════════════════════╗
║                         CROSS-COMPILATION                                ║
╚══════════════════════════════════════════════════════════════════════════╝

# Build for Linux
GOOS=linux GOARCH=amd64 go build -o vlp2ss-linux main.go

# Build for Windows
GOOS=windows GOARCH=amd64 go build -o vlp2ss.exe main.go

# Build for macOS (Intel)
GOOS=darwin GOARCH=amd64 go build -o vlp2ss-mac-intel main.go

# Build for macOS (Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -o vlp2ss-mac-arm main.go
`
	fmt.Println(examples)
}

// Helper functions for content block generation
func generateUUID() string {
	u, _ := uuid.NewRandom()
	return u.String()
}

func slugify(text string) string {
	// Convert to lowercase and replace spaces with hyphens
	text = strings.ToLower(text)
	text = strings.ReplaceAll(text, " ", "-")
	// Remove special characters
	reg := regexp.MustCompile("[^a-z0-9-]+")
	text = reg.ReplaceAllString(text, "")
	return text
}

func extractImagesFromHTML(htmlContent string) []map[string]string {
	images := []map[string]string{}
	// Simple regex to extract img tags
	imgRegex := regexp.MustCompile(`<img[^>]+src="([^"]+)"[^>]*>`)
	matches := imgRegex.FindAllStringSubmatch(htmlContent, -1)
	for _, match := range matches {
		if len(match) > 1 {
			// Unescape HTML entities (e.g., &amp; -> &)
			src := html.UnescapeString(match[1])

			// Extract just the filename, removing any query parameters
			// e.g., "image.png?X-Amz-Algorithm=..." -> "image.png"
			srcPath := src
			if idx := strings.Index(src, "?"); idx != -1 {
				srcPath = src[:idx]
			}

			filename := filepath.Base(srcPath)
			images = append(images, map[string]string{
				"src":      src,
				"filename": filename,
				"alt":      "",
			})
		}
	}
	return images
}

func removeImagesFromHTML(htmlContent string) string {
	imgRegex := regexp.MustCompile(`<img[^>]*>`)
	return imgRegex.ReplaceAllString(htmlContent, "")
}

func extractYouTubeEmbeds(htmlContent string) []string {
	if htmlContent == "" {
		return nil
	}
	// Use regex to find all html-embed divs
	re := regexp.MustCompile(`(?s)<div class="html-embed">.*?</div>`)
	return re.FindAllString(htmlContent, -1)
}

func removeYouTubeEmbedsFromHTML(htmlContent string) string {
	if htmlContent == "" {
		return ""
	}
	// Use regex to remove all html-embed divs
	re := regexp.MustCompile(`(?s)<div class="html-embed">.*?</div>`)
	return re.ReplaceAllString(htmlContent, "")
}

func extractStyledBlocksFromHTML(htmlContent string) []map[string]string {
	if htmlContent == "" {
		return nil
	}
	// Regex to find all screensteps-styled-block divs and capture the data-style and inner HTML
	re := regexp.MustCompile(`(?s)<div class="screensteps-styled-block" data-style="([^"]+)">(.*?)</div>`)
	matches := re.FindAllStringSubmatch(htmlContent, -1)

	var styledBlocks []map[string]string
	for _, match := range matches {
		if len(match) == 3 {
			styledBlocks = append(styledBlocks, map[string]string{
				"style": match[1],
				"html":  match[2],
			})
		}
	}
	return styledBlocks
}

func removeStyledBlocksFromHTML(htmlContent string) string {
	if htmlContent == "" {
		return ""
	}
	// Regex to remove all screensteps-styled-block divs
	re := regexp.MustCompile(`(?s)<div class="screensteps-styled-block"[^>]*>.*?</div>`)
	return re.ReplaceAllString(htmlContent, "")
}

func detectStyleFromHTML(htmlContent string) string {
	// Detect ScreenSteps styles from VLP HTML div classes
	if strings.Contains(htmlContent, "block-style-introduction") {
		return "introduction"
	}
	if strings.Contains(htmlContent, "block-style-tip") {
		return "tip"
	}
	if strings.Contains(htmlContent, "block-style-note") {
		return "note"
	}
	if strings.Contains(htmlContent, "block-style-warning") {
		return "warning"
	}
	return ""
}

func removeStyleDivs(htmlContent string) string {
	// Remove VLP-specific div wrappers while preserving inner content
	styleRegex := regexp.MustCompile(`<div class="block-style-[^"]*">(.*?)</div>`)
	return styleRegex.ReplaceAllString(htmlContent, "$1")
}

// CLI
func main() {
	var (
		inputPath    string
		outputDir    string
		verbose      bool
		noCleanup    bool
		showExamples bool
		upload       bool
		account      string
		user         string
		token        string
		siteID       string
		suffix       bool
	)

	rootCmd := &cobra.Command{
		Use:     "vlp2ss",
		Short:   "Convert VLP exported content to ScreenSteps format",
		Version: "1.0.2",
		Long: `VLP2SS - The VLP to ScreenSteps Converter

This tool converts VMware Lab Platform (VLP) exported content 
to ScreenSteps format with enhanced logging and progress tracking.

Version: 1.0.2
Author: Burke Azbill
License: MIT`,
		PersistentPreRun: func(cmd *cobra.Command, args []string) {
			// Read from environment variables if flags are not set
			if account == "" {
				account = os.Getenv("SS_ACCOUNT")
			}
			if user == "" {
				user = os.Getenv("SS_USER")
			}
			if token == "" {
				token = os.Getenv("SS_TOKEN")
			}
			if siteID == "" {
				siteID = os.Getenv("SS_SITE")
			}
		},
		Run: func(cmd *cobra.Command, args []string) {
			if showExamples {
				printExamples()
				return
			}

			if inputPath == "" {
				cmd.Help()
				fmt.Println("\nFor detailed examples, run with --examples")
				return
			}

			// Clean logs and output directories at startup
			if err := os.RemoveAll("logs"); err != nil && !os.IsNotExist(err) {
				fmt.Fprintf(os.Stderr, "Failed to clean logs directory: %v\n", err)
			}
			if err := os.MkdirAll("logs", 0755); err != nil {
				fmt.Fprintf(os.Stderr, "Failed to create logs directory: %v\n", err)
				os.Exit(1)
			}

			if err := os.RemoveAll(outputDir); err != nil && !os.IsNotExist(err) {
				fmt.Fprintf(os.Stderr, "Failed to clean output directory: %v\n", err)
			}
			if err := os.MkdirAll(outputDir, 0755); err != nil {
				fmt.Fprintf(os.Stderr, "Failed to create output directory: %v\n", err)
				os.Exit(1)
			}

			logger, err := NewLogger(verbose)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Failed to create logger: %v\n", err)
				os.Exit(1)
			}
			defer logger.Close()

			converter := NewConverter(logger)

			var outputPath string

			// Check if input is a file or directory
			info, err := os.Stat(inputPath)
			if err != nil {
				logger.Error(fmt.Sprintf("Input path does not exist: %s", inputPath))
				os.Exit(1)
			}

			if info.IsDir() {
				outputPath, err = converter.ConvertDirectory(inputPath, outputDir)
			} else if filepath.Ext(inputPath) == ".zip" {
				outputPath, err = converter.ConvertZip(inputPath, outputDir, !noCleanup)
			} else {
				logger.Error("Input must be a ZIP file or directory")
				os.Exit(1)
			}

			if err != nil {
				logger.Error(fmt.Sprintf("Conversion failed: %v", err))
				os.Exit(1)
			}

			// Upload if requested
			if upload {
				if account == "" || user == "" || token == "" || siteID == "" {
					logger.Error("Upload requires --account, --user, --token, and --site flags, or SS_ACCOUNT, SS_USER, SS_TOKEN, and SS_SITE environment variables.")
					os.Exit(1)
				}

				if err := UploadToScreenSteps(outputPath, account, user, token, siteID, logger, suffix); err != nil {
					logger.Error(fmt.Sprintf("Upload failed: %v", err))
					os.Exit(1)
				}
			}
		},
	}

	rootCmd.Flags().StringVarP(&inputPath, "input", "i", "", "Input VLP ZIP file or extracted directory")
	rootCmd.Flags().StringVarP(&outputDir, "output", "o", "output", "Output directory")
	rootCmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose logging")
	rootCmd.Flags().BoolVar(&noCleanup, "no-cleanup", false, "Keep temporary files after conversion")
	rootCmd.Flags().BoolVar(&showExamples, "examples", false, "Show detailed usage examples")
	rootCmd.Flags().BoolVar(&upload, "upload", false, "Upload to ScreenSteps after conversion")
	rootCmd.Flags().StringVar(&account, "account", "", "ScreenSteps account name")
	rootCmd.Flags().StringVar(&user, "user", "", "ScreenSteps user ID")
	rootCmd.Flags().StringVar(&token, "token", "", "ScreenSteps API token")
	rootCmd.Flags().StringVar(&siteID, "site", "", "ScreenSteps site ID")
	rootCmd.Flags().BoolVar(&suffix, "suffix", false, "Append -go to manual titles")

	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
