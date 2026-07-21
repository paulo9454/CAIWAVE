import { Wifi } from "lucide-react";

import { Button } from "../ui/button";

const VoucherPanel = ({
  voucherCode,
  setVoucherCode,
  redeemingVoucher,
  handleVoucherRedemption,
}) => (
  <div className="rounded-xl border border-blue-700/50 bg-gradient-to-br from-blue-950/80 to-indigo-950/60 p-5">
    <div className="mb-4">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-blue-300">
        <Wifi className="h-5 w-5" />
        Have a Voucher?
      </h2>

      <p className="mt-1 text-sm text-neutral-400">
        Enter your CAIWAVE voucher code to connect without making a payment.
      </p>
    </div>

    <div className="flex flex-col gap-3 sm:flex-row">
      <input
        type="text"
        value={voucherCode}
        onChange={(event) =>
          setVoucherCode(
            event.target.value
              .toUpperCase()
              .replace(/[^A-Z0-9-]/g, "")
              .slice(0, 32)
          )
        }
        onKeyDown={(event) => {
          if (event.key === "Enter" && !redeemingVoucher) {
            handleVoucherRedemption();
          }
        }}
        autoComplete="off"
        spellCheck={false}
        placeholder="Enter voucher code"
        className="min-w-0 flex-1 rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-3 font-mono uppercase tracking-wider text-white outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30"
      />

      <Button
        type="button"
        onClick={handleVoucherRedemption}
        disabled={redeemingVoucher || !voucherCode.trim()}
        className="bg-blue-600 px-6 py-3 text-white hover:bg-blue-700 sm:w-auto"
      >
        {redeemingVoucher ? (
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
        ) : (
          <>
            <Wifi className="mr-2 h-5 w-5" />
            Redeem Voucher
          </>
        )}
      </Button>
    </div>

    <p className="mt-3 text-xs text-neutral-500">
      Each voucher can only be redeemed once and is valid for its assigned
      hotspot.
    </p>
  </div>
);

export default VoucherPanel;
