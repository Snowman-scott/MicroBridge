class MicrobridgeLmd < Formula
  include Language::Python::Virtualenv

  desc "NDP/CSV to LMD Converter"
  homepage "https://github.com/Snowman-scott/MicroBridge"
  url "https://files.pythonhosted.org/packages/fa/f6/784f57b4cd8109626aef76896d5b3725c8c9ce6bd2f402f87142ab8538c3/microbridge_lmd-0.2.0.tar.gz"
  sha256 "028b0f69bbeece426616d0fde49067b3780fd5a5cbc9b24ad38cfb6ad2824d96"
  license "GPL-3.0-or-later"

  depends_on "python3"
  depends_on "python-tk@3.12"

  resource "click" do
    url "https://files.pythonhosted.org/packages/76/d4/81420972a676e8ffea40450d8c8c92943e7218a78fe9b64359836cc9876b/click-8.4.2.tar.gz"
    sha256 "9a6cea6e60b17ebe0a44c5cc636d94f09bd66142c1cd7d8b4cd731c4917a15f6"
  end

  resource "customtkinter" do
    url "https://files.pythonhosted.org/packages/c4/36/aee6ed9171a5a232da66a8b257752bd03d25b487c9d67ba367ad159bd976/customtkinter-6.0.0.tar.gz"
    sha256 "c782df167bc64ab3fc3140286df06967ac2de4dcc97dd5958426fe9c1a98057b"
  end

  resource "darkdetect" do
    url "https://files.pythonhosted.org/packages/45/77/7575be73bf12dee231d0c6e60ce7fb7a7be4fcd58823374fc59a6e48262e/darkdetect-0.8.0.tar.gz"
    sha256 "b5428e1170263eb5dea44c25dc3895edd75e6f52300986353cd63533fe7df8b1"
  end

  resource "packaging" do
    url "https://files.pythonhosted.org/packages/7d/fa/3944b40b07da9ce895c0e6303a5ab7d53da063554f534556b134a54d6093/packaging-26.3.tar.gz"
    sha256 "94edc256424af38762eb31306eed28beb9f0efc50a8837492c9d6fd6004aed79"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/microbridge", "--help"
  end
end
