class MicrobridgeLmdDev < Formula
  include Language::Python::Virtualenv

  desc "NDP/CSV to LMD Converter (development preview)"
  homepage "https://github.com/Snowman-scott/MicroBridge"
  url "https://files.pythonhosted.org/packages/57/f1/22cd37af6bf9fd2a8a37caa103156117ec9f695d5920c809a0a12a74f457/microbridge_lmd-2.1.0.dev0.tar.gz"
  # Stated explicitly: Homebrew reads "0" out of a .dev0 filename, which would
  # put the keg in Cellar/microbridge-lmd-dev/0.
  version "2.1.0.dev0"
  sha256 "8e73751549bd69338364f2ee0539f6fc1eeaa3db527e4b99a4f500f4427e1e4d"
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
    # Built by hand rather than with virtualenv_install_with_resources: that
    # helper links every console script as-is, which would put a second
    # bin/microbridge in the prefix and collide with the stable formula.
    # "python3.14", not "python@3.14": this takes an interpreter to exec, not a
    # formula name. virtualenv_install_with_resources strips the @ for you.
    venv = virtualenv_create(libexec, "python3.14")
    venv.pip_install resources
    venv.pip_install buildpath

    # The whole point of this formula: linked under a -dev name so it installs
    # alongside microbridge-lmd instead of conflicting with it.
    bin.install_symlink libexec/"bin/microbridge" => "microbridge-dev"

    # macOS has no .desktop files; the equivalent is a .app bundle. Build a
    # thin one whose stub execs the CLI with no arguments, which is the branch
    # main.py sends to the GUI.
    return unless OS.mac?

    app = prefix/"MicroBridge Dev.app"
    (app/"Contents/MacOS").mkpath
    resources_dir = app/"Contents/Resources"
    resources_dir.mkpath

    ico = Dir[libexec/"lib/python*/site-packages/MicroBridge/resources/MicroBridge_Icon.ico"].first
    if ico
      iconset = buildpath/"MicroBridgeDev.iconset"
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
      system "iconutil", "-c", "icns", iconset, "-o", resources_dir/"MicroBridgeDev.icns"
    end

    (app/"Contents/MacOS/MicroBridgeDev").write <<~SH
      #!/bin/sh
      # opt_bin, not the versioned Cellar path, so upgrades do not orphan this.
      exec "#{opt_bin}/microbridge-dev"
    SH
    chmod 0755, app/"Contents/MacOS/MicroBridgeDev"

    # A distinct CFBundleIdentifier and name, otherwise Launchpad and Spotlight
    # treat this bundle as the stable one and only ever show a single entry.
    (app/"Contents/Info.plist").write <<~XML
      <?xml version="1.0" encoding="UTF-8"?>
      <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
        "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
      <plist version="1.0">
      <dict>
        <key>CFBundleName</key><string>MicroBridge Dev</string>
        <key>CFBundleDisplayName</key><string>MicroBridge Dev</string>
        <key>CFBundleExecutable</key><string>MicroBridgeDev</string>
        <key>CFBundleIdentifier</key><string>io.github.snowman-scott.microbridge-dev</string>
        <key>CFBundleIconFile</key><string>MicroBridgeDev</string>
        <key>CFBundlePackageType</key><string>APPL</string>
        <key>CFBundleShortVersionString</key><string>#{version}</string>
        <key>CFBundleVersion</key><string>#{version}</string>
        <key>NSHighResolutionCapable</key><true/>
      </dict>
      </plist>
    XML
  end

  def caveats
    <<~EOS
      This is a development preview and installs alongside microbridge-lmd.
      Run it as:
        microbridge-dev

      The stable `microbridge` command is untouched.

      Reference points are matched by title (ref_1, ref_2, ref_3) wherever they
      sit in the file. Files with no ref_N titles fall back to the old
      first-three-regions rule and warn.

      Note: `microbridge-dev --install-launcher` writes the same
      ~/Applications/MicroBridge.app as the stable build and will overwrite it.
      On macOS, open the dev GUI from #{opt_prefix}/MicroBridge Dev.app instead.
    EOS
  end

  test do
    system bin/"microbridge-dev", "--help"
    # Exercises the GUI import chain: `from tkinter import filedialog`
    # fails outright unless python-tk matches the venv's Python.
    system libexec/"bin/python", "-c", "from MicroBridge.GUI import gui"

    # The reference points sit last here, which only a ref_N-aware build
    # converts: the stable release would read ROI_1 as a calibration point.
    (testpath/"sample.ndpa").write <<~XML
      <?xml version="1.0"?>
      <annotations>
        <ndpviewstate id="1"><title>ROI_1</title><annotation type="freehand">
          <pointlist><point><x>300000000</x><y>400000000</y></point></pointlist>
        </annotation></ndpviewstate>
        <ndpviewstate id="2"><title>ref_1</title>
          <annotation type="circle"><x>100000000</x><y>200000000</y></annotation></ndpviewstate>
        <ndpviewstate id="3"><title>ref_2</title>
          <annotation type="circle"><x>150000000</x><y>250000000</y></annotation></ndpviewstate>
        <ndpviewstate id="4"><title>ref_3</title>
          <annotation type="circle"><x>200000000</x><y>300000000</y></annotation></ndpviewstate>
      </annotations>
    XML

    system bin/"microbridge-dev", testpath/"sample.ndpa"
    output = (testpath/"sample_LMD.xml").read
    assert_match "<X_CalibrationPoint_1>100000</X_CalibrationPoint_1>", output
    assert_match "<Y_CalibrationPoint_3>300000</Y_CalibrationPoint_3>", output
    assert_match "<ShapeCount>1</ShapeCount>", output
  end
end
