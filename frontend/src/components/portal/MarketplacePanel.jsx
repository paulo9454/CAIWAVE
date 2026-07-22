import {
  ExternalLink,
  MessageCircle,
} from "lucide-react";

import SmartCampaignMedia from "./SmartCampaignMedia";

const MarketplacePanel = ({
  sponsorCards,
  baseUrl,
  formatWhatsApp,
}) => (
  <section
    id="marketplace"
    className="scroll-mt-5 rounded-[1.75rem] border border-white/10 bg-neutral-900/90 p-4 shadow-xl shadow-black/20 sm:p-5"
  >
    <div className="mb-4 flex items-start justify-between gap-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wider text-purple-400">
          Advertising Marketplace
        </p>

        <h2 className="mt-1 text-lg font-semibold text-white">
          Sponsored Campaigns
        </h2>

        <p className="mt-1 text-sm text-neutral-400">
          Discover offers, services and promotions from local businesses.
        </p>
      </div>

      <span className="shrink-0 rounded-full border border-purple-500/30 bg-purple-500/10 px-3 py-1 text-xs font-medium text-purple-300">
        Swipe
      </span>
    </div>

    <div
      className="-mx-1 flex snap-x snap-mandatory gap-3 overflow-x-auto px-1 pb-3 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      style={{ msOverflowStyle: "none" }}
    >
      {sponsorCards.map((ad, index) => {
        const isPlaceholder = ad.id?.startsWith("sponsor-placeholder");

        return (
          <article
            key={ad.id || index}
            className="min-w-[78%] snap-start overflow-hidden rounded-xl border border-neutral-700 bg-neutral-800 sm:min-w-[46%] md:min-w-[31%]"
          >
            {!isPlaceholder && ad.media_url ? (
              <SmartCampaignMedia
                src={`${baseUrl}${ad.media_url}`}
                alt={ad.title}
                mediaType="image"
                mediaKey={ad.id || ad.media_url}
              >
                <span className="absolute left-2 top-2 rounded-full border border-white/10 bg-black/50 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-white">
                  Sponsor
                </span>
              </SmartCampaignMedia>
            ) : (
              <div className="relative aspect-video overflow-hidden bg-gradient-to-br from-purple-950 via-indigo-900 to-blue-900">
                <div className="flex h-full w-full items-center justify-center p-6 text-center">
                  <div>
                    <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl border border-white/20 bg-white/10">
                      <span className="text-2xl" aria-hidden="true">
                        {ad.symbol || "⭐"}
                      </span>
                    </div>

                    <p className="text-sm font-semibold text-white">
                      Sponsored Placement
                    </p>
                  </div>
                </div>

                <span className="absolute left-2 top-2 rounded-full border border-white/10 bg-black/50 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-white">
                  Sponsor
                </span>
              </div>
            )}

            <div className="p-3">
              <h3 className="truncate font-semibold text-white">{ad.title}</h3>

              <p className="mt-1 text-sm text-neutral-400">
                {ad.description ||
                  "View this sponsored campaign on CAIWAVE WiFi."}
              </p>

              {!isPlaceholder && (
                <div className="mt-3 flex flex-wrap gap-3">
                  {ad.whatsapp_number && (
                    <a
                      href={`https://wa.me/${formatWhatsApp(
                        ad.whatsapp_number
                      )}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-sm font-medium text-green-400"
                    >
                      <MessageCircle className="h-4 w-4" />
                      WhatsApp
                    </a>
                  )}

                  {ad.click_url && (
                    <a
                      href={ad.click_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-sm font-medium text-blue-400"
                    >
                      <ExternalLink className="h-4 w-4" />
                      View offer
                    </a>
                  )}
                </div>
              )}
            </div>
          </article>
        );
      })}
    </div>

    <div className="flex items-center justify-center gap-2 pt-2">
      {sponsorCards.map((ad, index) => (
        <span
          key={`sponsor-indicator-${ad.id || index}`}
          className={`h-1.5 rounded-full transition-all ${
            index === 0
              ? "w-6 bg-purple-400"
              : "w-1.5 bg-neutral-600"
          }`}
        />
      ))}
    </div>

    <p className="pt-2 text-center text-xs text-neutral-500">
      Swipe horizontally to explore sponsored campaigns.
    </p>
  </section>
);

export default MarketplacePanel;
