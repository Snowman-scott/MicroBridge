class MicrobridgeLmd < Formula
  include Language::Python::Virtualenv

  desc "NDP/CSV to LMD Converter"
  homepage "https://github.com/Snowman-scott/MicroBridge"
  url "https://files.pythonhosted.org/packages/79/4a/b10abe90eb0cb3f0818b75cf0391ba0b64bcebab40be5999683839d95c87/microbridge_lmd-0.2.2.tar.gz"
  sha256 "455bfee331cc11e8f4dadcad7cd9ab349e48d5854e3ad4294307ad41fef2acb8"
  license "GPL-3.0-or-later"

  depends_on "python-tk@3.14"
  depends_on "python@3.14"

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
    virtualenv_install_with_resources using: "python@3.14"

    # macOS has no .desktop files; the equivalent is a .app bundle. Build a
    # thin one whose stub execs the CLI with no arguments, which is the branch
    # main.py sends to the GUI.
    return unless OS.mac?

    app = prefix/"MicroBridge.app"
    (app/"Contents/MacOS").mkpath
    resources_dir = app/"Contents/Resources"
    resources_dir.mkpath

    ico = Dir[libexec/"lib/python*/site-packages/MicroBridge/resources/MicroBridge_Icon.ico"].first
    if ico
      iconset = buildpath/"MicroBridge.iconset"
      iconset.mkpath
      # The source art is 256x256, so stop at the 256@2x slot rather than
      # upscaling into 512@2x.
      { "16x16" => 16, "16x16@2x" => 32, "32x32" => 32, "32x32@2x" => 64,
        "128x128" => 128, "128x128@2x" => 256, "256x256" => 256 }.each do |name, px|
        # -s format png is required: sips otherwise keeps the .ico format
        # regardless of the output suffix, and iconutil then rejects it.
        system "sips", "-s", "format", "png", "-z", px.to_s, px.to_s, ico,
               "--out", iconset/"icon_#{name}.png"
      end
      system "iconutil", "-c", "icns", iconset, "-o", resources_dir/"MicroBridge.icns"
    end

    (app/"Contents/MacOS/MicroBridge").write <<~SH
      #!/bin/sh
      # opt_bin, not the versioned Cellar path, so upgrades do not orphan this.
      exec "#{opt_bin}/microbridge"
    SH
    chmod 0755, app/"Contents/MacOS/MicroBridge"

    (app/"Contents/Info.plist").write <<~XML
      <?xml version="1.0" encoding="UTF-8"?>
      <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
        "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
      <plist version="1.0">
      <dict>
        <key>CFBundleName</key><string>MicroBridge</string>
        <key>CFBundleDisplayName</key><string>MicroBridge</string>
        <key>CFBundleExecutable</key><string>MicroBridge</string>
        <key>CFBundleIdentifier</key><string>io.github.snowman-scott.microbridge</string>
        <key>CFBundleIconFile</key><string>MicroBridge</string>
        <key>CFBundlePackageType</key><string>APPL</string>
        <key>CFBundleShortVersionString</key><string>#{version}</string>
        <key>CFBundleVersion</key><string>#{version}</string>
        <key>NSHighResolutionCapable</key><true/>
      </dict>
      </plist>
    XML
  end

  def caveats
    return unless OS.mac?

    <<~EOS
      A MicroBridge.app launcher was installed. Homebrew formulae cannot write
      to /Applications, so link it yourself to get it into Finder, Launchpad
      and Spotlight:
        ln -sfn #{opt_prefix}/MicroBridge.app /Applications/MicroBridge.app
    EOS
  end

  test do
    system bin/"microbridge", "--help"
    # Exercises the GUI import chain: `from tkinter import filedialog`
    # fails outright unless python-tk matches the venv's Python.
    system libexec/"bin/python", "-c", "from MicroBridge.GUI import gui"
  end
end
