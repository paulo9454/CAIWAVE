import { useEffect, useState } from "react";

const classifyOrientation = (width, height) => {
  if (!width || !height) return "landscape";

  const ratio = width / height;

  if (ratio >= 2) return "ultrawide";
  if (ratio >= 1.15) return "landscape";
  if (ratio >= 0.85) return "square";
  if (ratio >= 0.58) return "portrait";
  return "tall";
};

const aspectClasses = {
  ultrawide: "aspect-[21/9]",
  landscape: "aspect-video",
  square: "aspect-square",
  portrait: "aspect-[4/5]",
  tall: "aspect-[9/16]",
};

const fitClasses = {
  ultrawide: "object-cover",
  landscape: "object-cover",
  square: "object-cover",
  portrait: "object-contain",
  tall: "object-contain",
};

export default function SmartCampaignMedia({
  src,
  alt = "",
  mediaType = "image",
  mediaKey,
  className = "",
  autoPlay = false,
  muted = true,
  playsInline = true,
  preload = "metadata",
  controls = false,
  videoReady,
  onVideoLoadStart,
  onVideoLoadedData,
  onVideoCanPlay,
  onVideoPlaying,
  onVideoWaiting,
  onVideoEnded,
  fallback = null,
  children,
}) {
  const [orientation, setOrientation] = useState("landscape");
  const [imageReady, setImageReady] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setOrientation("landscape");
    setImageReady(false);
    setFailed(false);
  }, [src, mediaType]);

  const aspectClass =
    aspectClasses[orientation] || aspectClasses.landscape;

  const fitClass =
    fitClasses[orientation] || fitClasses.landscape;

  const shouldContain =
    orientation === "portrait" || orientation === "tall";

  if (!src || failed) {
    return (
      <div
        className={`relative aspect-video w-full overflow-hidden bg-neutral-900 ${className}`}
      >
        {fallback}
        {children}
      </div>
    );
  }

  return (
    <div
      className={`relative w-full overflow-hidden bg-neutral-800 transition-[aspect-ratio] duration-300 ${aspectClass} ${className}`}
      data-media-orientation={orientation}
    >
      {mediaType === "video" ? (
        <>
          <video
            key={mediaKey || src}
            src={src}
            className={`h-full w-full ${fitClass} transition-opacity duration-300 ${
              videoReady === false ? "opacity-0" : "opacity-100"
            }`}
            autoPlay={autoPlay}
            muted={muted}
            playsInline={playsInline}
            preload={preload}
            controls={controls}
            onLoadStart={(event) => {
              onVideoLoadStart?.(event);
            }}
            onLoadedMetadata={(event) => {
              const video = event.currentTarget;

              setOrientation(
                classifyOrientation(video.videoWidth, video.videoHeight)
              );
            }}
            onLoadedData={(event) => {
              onVideoLoadedData?.(event);
            }}
            onCanPlay={(event) => {
              onVideoCanPlay?.(event);
            }}
            onPlaying={(event) => {
              onVideoPlaying?.(event);
            }}
            onWaiting={(event) => {
              onVideoWaiting?.(event);
            }}
            onEnded={(event) => {
              onVideoEnded?.(event);
            }}
            onError={() => setFailed(true)}
          />

          {videoReady === false && (
            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-neutral-900 via-neutral-800 to-neutral-900">
              <div className="text-center">
                <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                <p className="mt-3 text-sm font-medium text-neutral-300">
                  Loading campaign…
                </p>
              </div>
            </div>
          )}
        </>
      ) : (
        <>
          {shouldContain && (
            <img
              src={src}
              alt=""
              aria-hidden="true"
              className="absolute inset-0 h-full w-full scale-110 object-cover opacity-35 blur-2xl"
            />
          )}

          <img
            key={mediaKey || src}
            src={src}
            alt={alt}
            className={`relative h-full w-full ${fitClass} transition-opacity duration-300 ${
              imageReady ? "opacity-100" : "opacity-0"
            }`}
            onLoad={(event) => {
              const image = event.currentTarget;

              setOrientation(
                classifyOrientation(
                  image.naturalWidth,
                  image.naturalHeight
                )
              );
              setImageReady(true);
            }}
            onError={() => setFailed(true)}
          />

          {!imageReady && (
            <div className="absolute inset-0 animate-pulse bg-white/[0.05]" />
          )}
        </>
      )}

      {children}
    </div>
  );
}
