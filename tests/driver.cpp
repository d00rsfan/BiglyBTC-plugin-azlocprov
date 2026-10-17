#include "biglybtc/plugin_host.hpp"
#include <arpa/inet.h>
#include <fcntl.h>
#include <unistd.h>
#include <cstring>
#include <cstdlib>
#include <iostream>
#include <vector>
#include <unicode/uloc.h>
#include <unicode/ustring.h>
bt_status countryName(void*, const char* code, const char* locale, bt_buffer_v1* output) noexcept {
  try {
    const auto countryLocale = std::string("_") + code;
    if (std::strlen(uloc_getISO3Country(countryLocale.c_str())) != 3) { return BT_NOT_FOUND; }
    UErrorCode status = U_ZERO_ERROR;
    UChar country[256]{};
    const auto length = uloc_getDisplayCountry(countryLocale.c_str(), locale, country, 256, &status);
    if (U_FAILURE(status)) { return BT_FAILED; }
    int32_t written = 0;
    u_strToUTF8(reinterpret_cast<char*>(output->data), static_cast<int32_t>(output->capacity),
        &written, country, length, &status);
    output->size = static_cast<std::uint32_t>(written) + 1;
    return status == U_BUFFER_OVERFLOW_ERROR ? BT_BUFFER_SMALL : U_SUCCESS(status) ? BT_OK : BT_FAILED;
  } catch (...) { return BT_FAILED; }
}
int main(int argc, char** argv) {
  if (argc < 5) { return 2; }
  const int directory = ::open(argv[2], O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
  if (directory < 0) { return 3; }
  const bt_plugin_options_v1 options{sizeof(options), BT_PLUGIN_ABI_V1, directory, 0, argv[3], nullptr, countryName};
  const auto* expectedVersion = std::getenv("BIGLYBTC_EXPECTED_NATIVE_VERSION");
  auto module = biglybtc::plugins::Module::load(argv[1], "azlocprov", BT_CAP_LOCATION, options,
      expectedVersion ? expectedVersion : "");
  ::close(directory);
  if (!module) { std::cerr << module.error().message << '\n'; return 4; }
  if (std::string_view(argv[4]) == "flag") {
    if (argc != 7 || std::strlen(argv[5]) != 2) { return 2; }
    bt_flag_request_v1 request{};
    std::memcpy(request.iso3166, argv[5], 2); request.size_index = std::stoi(argv[6]);
    bt_buffer_v1 output{};
    auto status = module->call(BT_LOCATION_FLAG, &request, sizeof(request), &output, sizeof(output));
    if (status == BT_BUFFER_SMALL) {
      std::vector<std::uint8_t> buffer(output.size);
      output.data = buffer.data(); output.capacity = static_cast<std::uint32_t>(buffer.size());
      status = module->call(BT_LOCATION_FLAG, &request, sizeof(request), &output, sizeof(output));
      if (status != BT_OK) { return 5; }
      std::cout.write(reinterpret_cast<const char*>(buffer.data()), output.size); return 0;
    }
    return status == BT_NOT_FOUND ? 10 : 5;
  }
  if (argc != 6 || std::strlen(argv[5]) >= 64) { return 2; }
  bt_location_request_v1 request{};
  request.family = std::strchr(argv[4], ':') ? 6 : 4;
  if (::inet_pton(request.family == 4 ? AF_INET : AF_INET6, argv[4], request.address) != 1) { return 2; }
  std::strcpy(request.locale, argv[5]);
  bt_location_result_v1 result{};
  const auto status = module->call(BT_LOCATION_LOOKUP, &request, sizeof(request), &result, sizeof(result));
  if (status == BT_NOT_FOUND) { return 10; }
  if (status != BT_OK) { return 5; }
  std::cout << result.iso3166 << '\t' << result.country << '\n';
}
